# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

class ArtProductionLineGroup(models.Model):
    _name = 'art.production.line.group'
    _description = 'Art Production Line Group'

    name = fields.Char(string="Group")
    sale_id = fields.Many2one('sale.order',
        string="Sale Order")
    art_production_id = fields.Many2one('art.production', string="Art Work", compute="get_art_production_id", store=True)
    art_lines = fields.One2many('art.production.line',
        'art_line_group_id', string="Linked Art Lines")

    so_lines = fields.One2many(
        'sale.order.line', 'dec_group_id',
        string='Sale Order Lines', copy=False)

    product_tmpl_id = fields.Many2one('product.template',
        string="Product Templatae")
    partner_id = fields.Many2one('res.partner',
        string="Partner")
    description = fields.Text(string="Description")
    customer_prefix = fields.Char(string="Customer Prefix",
                              help="Customer Prefix is used to generate unique Decoration Group",
                              compute="compute_customer_prefix", store=True)
    parent_id = fields.Many2one('res.partner', string="Parent")

    origin_partner_id = fields.Many2one('res.partner', string="Origin Partner")

    imprint_method = fields.Char("Decoration Mehod")
    imprint_location = fields.Char("Decoration Location")
    imprint_method_id = fields.Many2one('decoration.method',"Decoration Mehod ID")
    imprint_location_id = fields.Many2one('decoration.location',"Decoration Location ID")
    decoration_pricelist_id = fields.Many2one('decoration.pricelist',
        string="Decoration Pricelist")
    pms_code = fields.Many2many('product.decoration.pms.code', string="PMS Code")

    @api.depends('partner_id')
    def compute_customer_prefix(self):
        for rec in self:
            grand_parent = rec.partner_id.get_super_parent()
            if rec.partner_id:
                if rec.partner_id.customer_prefix:
                    rec.customer_prefix = rec.partner_id.customer_prefix
                elif rec.partner_id.parent_id.customer_prefix:
                    rec.customer_prefix = rec.partner_id.parent_id.customer_prefix
                else:
                    if grand_parent and not grand_parent.customer_prefix:
                        raise ValidationError("Parent Company %s has no Customer Prefix Set !" %(grand_parent.name))
                    rec.customer_prefix = grand_parent.customer_prefix
            else:
                if grand_parent and not grand_parent.customer_prefix:
                    raise ValidationError("Parent Company %s has no Customer Prefix Set !" %(grand_parent.name))
                rec.customer_prefix = grand_parent.customer_prefix





    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = ['|', ('name', operator, name), ('description', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.depends('art_lines')
    def get_art_production_id(self):
        for rec in self:
            art_id = False
            art_ids = rec.art_lines.mapped('art_id')
            if art_ids:
                art_id = art_ids[0]
            rec.art_production_id = art_id
            
    _sql_constraints = [
        ('name', 'unique(name)', 'Group Name already exist!')
    ]
    def name_get(self):
        if self._context.get('view_from_button', False):
            res = []
            for rec in self:
                if rec.description:
                    name = rec.name + " "+ rec.description
                    res.append((rec.id, name))
                else:
                    res.append((rec.id, rec.name))
            return res
        else:
            return super(ArtProductionLineGroup, self).name_get()

    @api.model
    def default_get(self, fields_list):
        defaults = super(ArtProductionLineGroup, self).default_get(fields_list)
        # Retrieve the current active record, if any
        partner_id = self._context.get('partner_id', False) or\
                     self._context.get('partner_id_dec', False)
        art_group_main_form_view = self._context.get('form_view_ref') if 'form_view_ref' in self._context \
            else False

        if partner_id:
            if art_group_main_form_view != 'bista_art_work.view_art_production_line_group_form':
                self._fields['name'].readonly = True
            partner_id_obj = self.env['res.partner'].browse(partner_id)
            # Use the values from the active record to pre-fill the form
            dec_name = partner_id_obj.get_decoration_name()
            if not dec_name:
                raise ValidationError("Prefix is not set on Customer ! Please check Customer configuration !")
            if dec_name:
                grand_parent = partner_id_obj.get_super_parent()
                defaults.update({
                    'name': dec_name[0],
                    'origin_partner_id': partner_id_obj.id,
                    'partner_id': grand_parent.id if grand_parent else partner_id_obj.id,
                    'parent_id': grand_parent.id if grand_parent else partner_id_obj.id,
                })

        return defaults

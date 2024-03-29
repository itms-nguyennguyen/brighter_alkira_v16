# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_aftercare_id = fields.Many2one(
        'document.page', 
        string="Aftercare",
        domain=[('type', '=', 'content'), ('parent_id.name', '=', 'After Care')])

    aftercare_id = fields.Many2one(
        'bureaucrat.knowledge.document',
        string="Aftercare",
        domain=[('category_id.name', '=', 'After Care')])
    

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_aftercare_id = fields.Many2one(
        'document.page',
        string="Aftercare Template",
        domain=[('type', '=', 'content'), ('parent_id.name', '=', 'After Care')])

    aftercare_id = fields.Many2one(
        'bureaucrat.knowledge.document',
        string="Aftercare Template",
        compute='_compute_default_aftercare_id',
        inverse='_inverse_default_aftercare_id',
        domain=[('category_id.name', '=', 'After Care')])

    @api.depends('product_variant_ids', 'product_variant_ids.default_aftercare_id')
    def _compute_default_aftercare_id(self):
        for template in self:
            template.aftercare_id = template.product_variant_ids[0].aftercare_id
    
    def _inverse_default_aftercare_id(self):
        for template in self:
            for variant_id in template.product_variant_ids:
                variant_id.aftercare_id = template.aftercare_id

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_product_id_set_qty(self):
        for line in self:
            if line.product_id.min_qty:
                line.write({'product_uom_qty':line.product_id.min_qty})

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty_set_qty(self):
        for line in self:
            if line.product_id.min_qty:
                if line.product_uom_qty < line.product_id.min_qty:
                    raise ValidationError(_(
                        "Minimum Order Quantity for '%s' is %s."%(self.product_id.display_name,self.product_id.min_qty),
                    ))

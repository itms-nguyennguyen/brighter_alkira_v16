from odoo import models, fields, api, _
from odoo.tools import get_lang

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    delivery_sale_line_ids = fields.One2many(
        'sale.order.line', 
        'delivery_purchase_order_id', 
        compute="_compute_delivery_sale_line_ids", 
        string='Sale Order Lines')
    
    def _compute_delivery_sale_line_ids(self):
        for order in self:
            order.delivery_sale_line_ids = order.order_line.move_dest_ids.sale_line_id | order.order_line.move_ids.move_dest_ids.sale_line_id

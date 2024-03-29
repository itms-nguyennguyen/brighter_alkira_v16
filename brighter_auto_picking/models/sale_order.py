from odoo import models, fields, api, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # note_po_line_id = fields.Many2one('purchase.order.line', string='Note PO Line')
    delivery_purchase_order_id = fields.Many2one('purchase.order', string='Delivery Purchase Order')

    def _compute_delivery_purchase_order_id(self):
        for line in self:
            line.delivery_purchase_order_id = \
                line.move_ids and \
                line.move_ids.created_purchase_line_id and \
                line.move_ids.created_purchase_line_id[0].id or False
            
    # def _action_launch_stock_rule(self, previous_product_uom_qty=False):
    #     res = super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
    #     for line in self:
    #     purchase_lines = line.move_ids.created_purchase_line_id | line.move_ids.move_orig_ids.purchase_line_id
    #     line.make_note_line(purchase_lines)
    #     return res
    
    # def make_note_line(self, purchase_lines):
    #     self.ensure_one()
    #     note_line = self.env['purchase.order.line'].search([
    #         ('source_so_line_id', '=', self.id),
    #         ('display_type', '=', 'line_note'),
    #         ('source_po_line_id', '=', purchase_lines.id)])
    #     if note_line:
    #         note_line.write({
    #             'name': _('%s deliver to %s') % (self.product_uom_qty, self.order_id.partner_shipping_id._display_address()),
    #         })
    #         return True
    #     self.env['purchase.order.line'].create({
    #         'name': _('%s deliver to %s') % (self.product_uom_qty, self.order_id.partner_shipping_id._display_address()),
    #         'order_id': purchase_lines.order_id.id,
    #         'product_qty': 0,
    #         'product_uom': self.product_uom.id,
    #         'price_unit': 0,
    #         'source_po_line_id': purchase_lines.id,
    #         'source_so_line_id': self.id,
    #         'date_planned': fields.Datetime.now(),
    #         'taxes_id': [(6, 0, [])],
    #         'display_type': 'line_note',
    #     })
        
        # return True
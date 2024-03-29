from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if not self.move_ids:
            return res
        dest_moves = self.move_ids.mapped('move_dest_ids')
        if not dest_moves:
            return res
        dest_pickings = dest_moves.mapped('picking_id')
        if not dest_pickings:
            return res
        dest_pickings.action_assign()
        dest_pickings.action_set_quantities_to_reservation()
        dest_pickings.filtered(
            lambda p: p.state == 'assigned').with_context(
                skip_immediate=True, skip_sms=True).button_validate()
        return res

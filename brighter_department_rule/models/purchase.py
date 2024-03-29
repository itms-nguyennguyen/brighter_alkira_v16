from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def default_department_id(self):
        # if self.env.user.department_ids and len(self.env.user.department_ids) == 1:
        #     return self.env.user.department_ids[0]
        return False
    
    department_id = fields.Many2one('hr.department', string='Department',
                                    default=lambda self: self.default_department_id())

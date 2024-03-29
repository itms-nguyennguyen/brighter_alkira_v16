from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def default_department_id(self):
        if self.env.user.department_ids and len(self.env.user.department_ids) == 1:
            return self.env.user.department_ids[0]
        return False
    
    department_id = fields.Many2one('hr.department', string='Department',
                                    default=lambda self: self.default_department_id())

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('website_id', False):
                user = self.env['res.users'].sudo().browse([self.env.context.get('uid', False)])
                if user:
                    vals['department_id'] = user.department_ids and user.department_ids[0].id or False
        return super().create(vals_list)
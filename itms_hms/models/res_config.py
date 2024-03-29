from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_single_booking = fields.Boolean("Is Single Booking", default=False)


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_single_booking = fields.Boolean("Is Single Booking", related='company_id.is_single_booking', store=True,
                                       readonly=False)

    def get_values(self):
        res = super(WebsiteConfigSettings, self).get_values()
        res.update(is_single_booking=self.env['ir.config_parameter'].sudo().get_param('is_single_booking'))
        return res

    def set_values(self):
        super(WebsiteConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('is_single_booking', self.is_single_booking)


class Users(models.Model):
    _inherit = 'res.users'

    position_type = fields.Selection([('Prescriber', 'Prescriber'), ('Nurses', 'Nurse'), ('Patient', 'Patient')],
                                     default='Nurses',
                                     string='Position Type')

    # patient_ids = fields.One2many('res.partner', 'nurses_id', string='Patients')

    @api.model_create_multi
    def create(self, vals_list):
        users = super(Users, self).create(vals_list)
        for user in users:
            user.partner_id.position_type = user.position_type
        return users

    def write(self, values):
        if 'position_type' in values:
            for user in self:
                user.partner_id.position_type = values.get('position_type')
        res = super(Users, self).write(values)
        return res

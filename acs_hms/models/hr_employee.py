# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    signature = fields.Binary('Signature')
    registration_insurance = fields.Binary(string="Registration Insurance", groups="hr.group_hr_user", tracking=True)


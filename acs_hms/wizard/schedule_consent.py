# coding: utf-8

from odoo import models, api, fields


class ScheduleConsent(models.TransientModel):
    _name = 'schedule.consent.wiz'
    _description = "Schedule Consent"

    def proceed_appointment(self):
        appointment = self.env['hms.appointment'].search([('id', '=', self.env.context.get('active_id'))])
        appointment.state = 'confirm_consent'
        return True


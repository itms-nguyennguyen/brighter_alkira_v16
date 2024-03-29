from odoo import models, _


class ACSPatient(models.Model):
    """
    Inheriting model 'res.partner' to add the function to send SMS.
    Methods:
        send_sms():
            Opens the Send SMS wizard.
    """
    _inherit = 'hms.patient'

    def twilio_send_sms(self):
        self.ensure_one()
        record_ids = self.id
        numbers = self.env['hms.patient'].browse(record_ids).mapped('phone')
        return {
            'name': _('Send SMS'),
            'type': 'ir.actions.act_window',
            'res_model': 'twilio.sms.send',
            # self.env.ref('itms_consent_form.view_aftercare_tree').id,
            'view_id': self.env.ref('twilio_sms_gateway_gsc.twilio_sms_send_from_view_simple').id,
            'context': {
                'manual_sms': True,
                'default_send_sms_to': 'single_contact',
                'default_partner_id': self.partner_id.id,
                'default_patient_id': self.id
                # 'default_sms_to': ','.join([str(numb) for numb in numbers]),
            },
            'view_mode': 'form',
            'target': 'new'
        }


class Appointment(models.Model):
    _inherit = 'hms.appointment'

    def twilio_send_sms(self):
        self.ensure_one()
        record_ids = self.id
        numbers = self.env['hms.appointment'].browse(record_ids).mapped('mobile')
        return {
            'name': _('Send SMS'),
            'type': 'ir.actions.act_window',
            'res_model': 'twilio.sms.send',
            'view_id': self.env.ref('twilio_sms_gateway_gsc.twilio_sms_send_from_view_simple').id,
            'context': {
                'manual_sms': True,
                'default_send_sms_to': 'single_contact',
                'default_partner_id': self.patient_id.partner_id.id,
                'default_patient_id': self.patient_id.id
                # 'default_sms_to': ','.join([str(numb) for numb in numbers]),
            },
            'view_mode': 'form',
            'target': 'new'
        }

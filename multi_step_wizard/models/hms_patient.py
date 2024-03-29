from odoo import api, fields, models, _


class ACSPatient(models.Model):
    _inherit = "hms.patient"

    def create_appointment_wizard(self):
        return {
            'name': _('Create Appointment'),
            'type': 'ir.actions.act_window',
            'res_model': 'my.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('multi_step_wizard.my_wizard_form').id,
            'target': 'new',
            # 'context': {'default_patient_id': self.id}
        }
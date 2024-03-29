from odoo import models, fields, api


class MyWizard(models.TransientModel):
    _name = 'my.wizard'
    _inherit = ['multi.step.wizard.mixin']
    _description = 'Create Apointment Wizard'

    patient_id = fields.Many2one(
        'hms.patient', 
        ondelete='cascade', 
        string='Patient',
        default=lambda self: self._default_patient_id())
    nurse_id = fields.Many2one(
        comodel_name='res.users',
        name="Nurse",
        required=True,
        default=lambda self: self.env.user.id,
    )
    consultation_type = fields.Selection([
        ('adverse', 'Adverse Event'),
        ('consultation', 'Consultation'),
        ('consultation_prescription', 'Consultation and Prescription'),
        ('followup', 'Follow-Up Appointment')], 'Consultation Type', default='consultation_prescription',
        copy=False)
    date = fields.Date("Date")
    prescription_ids = fields.Many2many(
        comodel_name='prescription.order',
        relation='prescription_wizard_rel',
        column1='prescription_id',
        column2='wizard_id',
        string='Prescriptions',
    )
    # prescription_id = fields.Many2one(
    #     comodel_name='prescription.order',
    #     string='Prescription',
    # ) 
    
    @api.model
    def _selection_state(self):
        return [
            ('start', 'Start'),
            ('date', 'Date Time'),
            ('prescription', 'Prescription'),
            ('final', 'Consultation Type'),
        ]
    
    @api.model
    def _default_patient_id(self):
        return self.env.context.get('active_id')
    
    def state_exit_start(self):
        self.state = 'date'

    def state_exit_date(self):
        self.state = 'prescription'

    def state_exit_prescription(self):
        self.state = 'final' 

    def button_done(self):
        self.ensure_one()
        #create the appointment with self values
        vals = {
            'patient_id': self.patient_id.id,
            'nurse_id': self.nurse_id.id,
            'schedule_date': self.date,
            'consultation_type': self.consultation_type,
            'prescription_ids': [(6, 0, self.prescription_ids.ids)],
        }
        appointment = self.env['hms.appointment'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hms.appointment',
            'res_id': appointment.id,
            'view_mode': 'form',
            'target': 'current',
        }

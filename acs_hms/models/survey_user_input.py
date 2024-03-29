# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Survey(models.Model):
    _inherit = 'survey.survey'

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    # appointment_id = fields.One2many('hms.appointment', 'survey_response_id', string='Appointment')

    @api.model_create_multi
    def create(self, values_list):
        res = super().create(values_list)
        res.appointment_id = res.survey_id.appointment_id.id
        return res

    def _mark_done(self):
        res = super()._mark_done()
        for user_input in self:
            user_input.appointment_id.is_done_survey = True
            if user_input.appointment_id.state == 'confirm_consent':
                user_input.appointment_id.state = 'in_consultation'
        return res


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    appointment_id = fields.Many2one('hms.appointment', related='user_input_id.appointment_id', store=True,
                                     string='Appointment')
    suggested_answer_yes = fields.Boolean('Yes', compute='_compute_suggested_answer')
    suggested_answer_no = fields.Boolean('No', compute='_compute_suggested_answer')
    prescription_id = fields.Many2one('prescription.order', related='appointment_id.prescription_id', string='Prescription')

    @api.depends('suggested_answer_id')
    def _compute_suggested_answer(self):
        for record in self:
            record.suggested_answer_yes = False
            record.suggested_answer_no = False
            if record.suggested_answer_id:
                if str(record.suggested_answer_id.value).lower() == 'yes':
                    record.suggested_answer_yes = True
                if str(record.suggested_answer_id.value).lower() == 'no':
                    record.suggested_answer_no = True


class AppointmentIndividualSurveyAnswer(models.Model):
    _name = "appointment.individual.survey.answer"
    _description = "Individual"

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    name = fields.Char('Question')
    answer = fields.Char('Answer')
    yes = fields.Boolean('Yes')
    no = fields.Boolean('No')
    date = fields.Datetime()


class AppointmentRelevantSurveyAnswer(models.Model):
    _name = "appointment.relevant.survey.answer"
    _description = "Relevant"

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    name = fields.Char('Question')
    answer = fields.Char('Answer')
    yes = fields.Boolean('Yes')
    no = fields.Boolean('No')
    date = fields.Datetime()


class AppointmentMedicationSurveyAnswer(models.Model):
    _name = "appointment.medication.survey.answer"
    _description = "Medication"

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    name = fields.Char('Question')
    answer = fields.Char('Answer')
    yes = fields.Boolean('Yes')
    no = fields.Boolean('No')
    date = fields.Datetime()


class AppointmentAdditionSurveyAnswer(models.Model):
    _name = "appointment.addition.survey.answer"
    _description = "Additional"

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    name = fields.Char('Question')
    answer = fields.Char('Answer')
    yes = fields.Boolean('Yes')
    no = fields.Boolean('No')
    date = fields.Datetime()

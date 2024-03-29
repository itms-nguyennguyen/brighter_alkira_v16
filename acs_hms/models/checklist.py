# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MedicalChecklistTemplate(models.Model):
    _name = 'medical.checklist'
    _description = 'Medical Checklist'

    name = fields.Char('Name')
    detail_ids = fields.One2many('medical.checklist.line', 'checklist_id', string='Questions')


class MedicalChecklistLine(models.Model):
    _name = 'medical.checklist.line'

    name = fields.Char('Name')
    checklist_id = fields.Many2one('medical.checklist', string='Checklist')


class PatientMedicalChecklistLine(models.Model):
    _name = 'patient.medical.checklist.line'

    name = fields.Char('Notes')
    question_id = fields.Many2one('medical.checklist.line', string='Question')
    checklist_id = fields.Many2one('medical.checklist', string='Checklist')
    yes = fields.Boolean('No/Yes')
    no = fields.Boolean('No')
    patient_id = fields.Many2one('hms.patient', string='Patient')
    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)

    @api.onchange('question_id', 'yes')
    def _onchange_choose_yes(self):
        if self.yes:
            self.no = False

    @api.onchange('question_id', 'no')
    def _onchange_choose_no(self):
        if self.no:
            self.yes = False

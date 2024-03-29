# -*- coding: utf-8 -*-
from odoo import api, fields, models
import json


class PatientDocument(models.Model):
    _inherit = 'patient.document'

    document_type = fields.Selection([
        ('front_view', 'Front View'),
        ('right_profile', 'Right Profile'),
        ('left_profile', 'Left Profile'),
        ('oblique_right', 'Oblique Right'),
        ('oblique_left', 'Oblique Left'),
        ('top_view', 'Top View'),
        ('bottom_view', 'Bottom View'),
        ('back_view', 'Back View')
    ], string='Document Type')
    instruction_pdf = fields.Binary('PDF')
    file_display = fields.Binary('file')
    instruction_type = fields.Selection([
        ('pdf', 'PDF'), ('image', 'Image')],
        string="Instruction", default="image"
    )
    display_type = fields.Selection([('before', 'Before'), ('after', 'After')], string='Type')

    def action_remove_record(self):
        for rec in self:
            rec.unlink()

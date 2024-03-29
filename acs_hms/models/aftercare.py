# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class AfterCare(models.Model):
    _inherit = 'patient.aftercare'

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')
    treatment_id = fields.Many2one('hms.treatment', string='Treatment')

    @api.onchange('knowledge_id')
    def onchange_knowledge_id(self):
        self.ensure_one()
        if self.knowledge_id:
            self.name = self.knowledge_id.name

    def action_open_form(self):
        # return the form view of this partner
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "bureaucrat.knowledge.document",
            "res_id": self.knowledge_id.id,
            "view_mode": "form",
            "view_type": "form",
            "views": [(False, "form")],
            "context": {'is_invisible': True, 'create': False, 'edit': False, 'is_display': True},
            "view_id": False,
            "target": "new",
        }

    def button_send_email(self):
        self.ensure_one()
        try:
            if self.appointment_id:
                template_aftercare = self.env.ref('acs_hms.appointment_aftercare_email')
                pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                    'itms_consent_form.action_report_aftercare', res_ids=[self.id])
                aftercare_attachment_id = self.env['ir.attachment'].create({
                    'name': self.name,
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': self._name,
                    'res_id': self.id
                })
                template_aftercare.attachment_ids = aftercare_attachment_id
                medicine_line_ids = []
                treatment_notes = []
                if self.appointment_id.treatment_ids:
                    for treat in self.appointment_id.treatment_ids:
                        if treat.state == 'done':
                            if treat.medicine_line_ids:
                                for line in treat.medicine_line_ids:
                                    if line.product_id:
                                        medicine_area = line.medicine_area or ''
                                        amount = line.amount or ''
                                        batch_number = line.acs_lot_id.name or ''
                                        medicine_technique = line.medicine_technique or ''
                                        medicine_depth = line.medicine_depth or ''
                                        medicine_method = line.medicine_method or ''
                                        product_name = line.sudo().product_id.name
                                        medicine_line_ids.append(
                                            {'product_name': product_name, 'medicine_area': medicine_area,
                                             'amount': amount,
                                             'batch_number': batch_number, 'medicine_technique': medicine_technique,
                                             'medicine_depth': medicine_depth, 'medicine_method': medicine_method,
                                             'template': treat.template_id.name})
                            if treat.template_id:
                                finding = treat.finding or ''
                                template = treat.template_id.name
                                treatment_notes.append({'template': template, 'finding': finding})
                email_values = {'medicine_line_ids': medicine_line_ids, 'treatment_notes': treatment_notes}
                is_sent = template_aftercare.with_context(**email_values).sudo().send_mail(self.appointment_id.id,
                                                                                           raise_exception=False,
                                                                                           force_send=True)
        except Exception as e:
            _logger.warning('Failed to send appointment Aftercare email: %s', e)

        return True

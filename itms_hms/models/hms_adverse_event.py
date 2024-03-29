# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import time

import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from babel.dates import format_datetime, format_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF, \
    format_datetime as tool_format_datetime
from odoo.tools.misc import formatLang
from odoo.release import version
from twilio.rest import Client
import re

class Adverse_Event(models.Model):
    _name = 'hms.adverse.event'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Adverse Event SMS"

    category_id = fields.Many2one('document.page',
                                  domain=[('type', '=', 'content'), ('parent_id.name', '=', 'Adverse Event')],
                                  string='Adverse Event')

    nurse_phone = fields.Char(string='Clinician Phone')
    content = fields.Char('Content')

    @api.onchange('nurse_id', 'patient_id', 'chemical_burns_event_boolean', 'medication_error_event_boolean', 'blindness_event_boolean', 'infections_event_boolean', 'allergic_event_boolean')
    def onchange_adverse_event_boolean(self):
        for rec in self:
            rec.content = ''
            if rec.nurse_id:
                rec.nurse_phone = rec.nurse_id.phone

            if rec.chemical_burns_event_boolean == True:
                rec.content += 'Chemical Burns,'

            if rec.medication_error_event_boolean == True:
                rec.content += 'Medication Errors,'

            if rec.blindness_event_boolean == True:
                rec.content += 'Blindness,'

            if rec.infections_event_boolean == True:
                rec.content += 'Infections,'

            if rec.allergic_event_boolean == True:
                rec.content += 'Allergic Reactions'

            rec.content = '''
            {}: Urgent - Adverse Event
            Nurse: {}
            Patient: {}
            Contact: {}
            Adverse Event: {}
            Please respond urgently.
            '''.format(
                rec.nurse_id.department_ids[0].name,
                rec.nurse_id.name,
                rec.patient_id.name,
                rec.nurse_phone,
                rec.content,
            )
                # for number in self.sms_to.split(','):
                #     if number:
                #         client.messages.create(
                #             body=self.text,
                #             from_=self.sms_id.twilio_phone_number,
                #             to=number
                #         )

    # @api.onchange('category_id')
    # def onchange_category_id(self):
    #     for rec in self:
    #         rec.content = None
    #         if rec.category_id:
    #             # Convert the HTML content to text
    #             text_content = re.sub(r'<[^>]+>', '', rec.category_id.content)
    #
    #             # Remove the `<data>` tags
    #             text_content = re.sub(r'<data>(.*?)</data>', '', text_content)
    #             rec.content = '''
    #                 {}:Urgent - Adverse Event \n
    #                 Nurse: {}\n
    #                 Patient: {}\n
    #                 Contact: {}\n
    #                 {}\n
    #                 Please respond urgently.\n
    #                 '''.format(
    #                 rec.company_id.name,
    #                 rec.nurse_id.name,
    #                 rec.patient_id.name,
    #                 rec.nurse_phone,
    #                 text_content,
    #             )
    def send_sms(self):
        for rec in self:
            rec.is_sent = False
            if rec.content:
                twilio_client = self.env['sms.gateway.config'].sudo().search([('gateway_name', '=', 'twilio')])
                client = Client(twilio_client.twilio_account_sid,
                                twilio_client.twilio_auth_token)

                rec.is_sent = client.messages.create(
                    body=rec.content,
                    from_=twilio_client.twilio_phone_number,
                    to='+61 0402851235'
                )
                self.env['sms.history'].sudo().create({
                    'sms_gateway_id': twilio_client.sms_gateway_id.id,
                    'sms_mobile': '+61 0402851235',
                    'sms_text': rec.content
                })

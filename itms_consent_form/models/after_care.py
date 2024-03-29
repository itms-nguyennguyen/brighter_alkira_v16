# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _, Command


class AfterCare(models.Model):
    _name = 'patient.aftercare'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Patient Aftercare"

    name = fields.Char('Title', required=1)
    content = fields.Html('Content')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'patient.aftercare')],
                                     string='Attachments')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env.company, store=True)

    category_id = fields.Many2one('document.page',
                                  domain=[('type', '=', 'content'), ('parent_id.name', '=', 'After Care')],
                                  string='Template')

    knowledge_id = fields.Many2one('bureaucrat.knowledge.document', domain=[('category_id.name', '=', 'After Care')],
                                   string='Template')


class AfterCareHistory(models.Model):
    _name = 'patient.aftercare.history'
    _description = "Patient Aftercare History"

    name = fields.Char('Title')
    aftercare_id = fields.Many2one('patient.aftercare', string="AfterCare", ondelete='cascade')
    patient_id = fields.Many2one('hms.patient', string="Patient", ondelete='cascade')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'patient.aftercare')],
                                     string='Attachments')
    state = fields.Selection([('sent', 'Sent'), ('fail', 'Delivery Failed')], string='Email Status')
    date = fields.Datetime('Date')
    user_id = fields.Many2one('res.users', 'By')

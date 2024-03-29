# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event')

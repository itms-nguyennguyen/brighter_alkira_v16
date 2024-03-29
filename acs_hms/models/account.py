# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Prescriber',
                                       index=True, help='Referring Prescriber', readonly=True,
                                       states={'draft': [('readonly', False)]})
    appointment_id = fields.Many2one('hms.appointment', string='Appointment', readonly=True,
                                     states={'draft': [('readonly', False)]})
    procedure_id = fields.Many2one('acs.patient.procedure', string='Patient Procedure', readonly=True,
                                   states={'draft': [('readonly', False)]})
    hospital_invoice_type = fields.Selection(
        selection_add=[('appointment', 'Appointment'), ('treatment', 'Treatment'), ('procedure', 'Procedure')])


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    prescription_id = fields.Many2one(
        string="Prescription", comodel_name='prescription.order', readonly=True)


class AccountMove(models.Model):
    _inherit = "account.move"

    prescription_id = fields.Many2one('prescription.order', string='Prescription')

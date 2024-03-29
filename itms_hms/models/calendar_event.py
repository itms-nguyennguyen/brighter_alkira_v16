# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    name = fields.Char('Meeting Subject', required=True)
    STATE_SELECTION = [('pending', 'Pending Confirmation'),
                       ('confirmed', 'Confirmed'),
                       ('treated', 'Treated'),
                       ('cancelled', 'Cancelled')]
    patient_id = fields.Many2one('hms.patient', string='Patient')
    start_at = fields.Date('Date', default=fields.Date.today)
    physician_id = fields.Many2one('hms.physician', string='Prescriber')
    state = fields.Selection(STATE_SELECTION, string='Appointment Status', default='pending')

    consultation_service = fields.Many2one('product.product', ondelete='restrict',
                                           string='Consultation Service',
                                           domain=[('hospital_product_type', '=', "consultation")])

    time_slot = fields.Many2one('appointment.schedule.slot.lines', string='Available Slots')
    payment_state = fields.Selection([('not_paid', 'Not Paid'),
                                      ('in_payment', 'In Payment'),
                                      ('paid', 'Paid')], default='not_paid', string='Payment Status')

    appointment_id = fields.Many2one('hms.appointment', string='Appointment')

    def write(self, values):
        res = super().write(values)
        return res

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        if self.patient_id:
            self.name = self.patient_id.partner_id.name

    def _prepare_invoice(self):
        self.ensure_one()
        vals = []
        for move_type in ['out_invoice', 'in_invoice']:
            vals.append({
                'move_type': move_type,
                'calendar_event_id': self.id,
                'narration': self.description,
                'currency_id': self.user_id.company_id.currency_id.id,
                'partner_id': self.patient_id.partner_id.id if move_type == 'out_invoice' else self.physician_id.partner_id.id,
                'partner_shipping_id': self.patient_id.partner_id.id if move_type == 'out_invoice' else self.physician_id.partner_id.id,
                'invoice_origin': self.name,
                'invoice_user_id': self.user_id.id,
                'company_id': self.user_id.company_id.id,
                'invoice_date': self.start_at,
                'invoice_line_ids': [],
            })
        return vals

    def _prepare_invoice_line(self):
        if not self.consultation_service:
            return
        return {
            'product_id': self.consultation_service.id,
            'quantity': 1,
            'price_unit': self.consultation_service.list_price,
            'name': self.consultation_service.name or self.name,
            'product_uom_id': self.consultation_service.uom_id.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if res:
            vals_app = {
                'schedule_date': res.start_at,
                'patient_id': res.patient_id.id,
                'notes': res.description,
                'product_id': res.consultation_service.id,
            }
            appointment_id = self.env['hms.appointment'].create(vals_app)
            if appointment_id:
                res.appointment_id = appointment_id.id
        return res

    # @api.onchange('physician_id')
    # def _onchange_physician_id(self):
    #     self.consultation_service = False
    #     self.time_slot = False
    #     result = {'domain': {'consultation_service': [('id', 'in', self.physician_id.consultaion_service_id.ids)],'time_slot': [('id', '=', self.physician_id.id)]}}
    #     return result

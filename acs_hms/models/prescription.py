# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID, Command
from odoo.exceptions import UserError
import logging

from dateutil.relativedelta import relativedelta
import uuid
from datetime import timedelta, datetime


class ACSPrescriptionOrder(models.Model):
    _name = 'prescription.order'
    _description = "Prescription Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'acs.qrcode.mixin']
    _order = 'id desc'

    @api.model
    def _current_user_doctor(self):
        physician_id = False
        ids = self.env['hms.physician'].search([('user_id', '=', self.env.user.id)])
        if ids:
            physician_id = ids[0].id
        return physician_id

    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)

    def get_clinic(self):
        return self.env.user.department_ids[0].id if len(self.env.user.department_ids) > 0 else False

    @api.model
    def _get_clinician(self):
        nurse_id = False
        ids = self.env['res.users'].search([('department_ids', 'in', self.env.user.department_ids.ids)])
        is_nurse = self.env.user.has_group('acs_hms_base.group_hms_manager')
        if is_nurse:
            nurse_id = self.env.user.id
        else:
            if ids:
                nurse_id = ids[0].id
        return nurse_id

    def _rec_count(self):
        for rec in self:
            rec.transaction_count = len(self.env['payment.transaction'].search(
                [('reference', '=', self.name), ('partner_id', '=', self.env.user.partner_id.id)]))
            rec.treatment_medicine_count = len(self.env['hms.treatment'].search(
                [('state', '=', 'done'), ('patient_id', '=', self.patient_id.id)]))

    READONLY_STATES = {'cancel': [('readonly', True)], 'prescription': [('readonly', True)],
                       'finished': [('readonly', True)], 'expired': [('readonly', True)],
                       'request': [('readonly', True)]}

    name = fields.Char(size=256, string='Number', help='Prescription Number of this prescription', readonly=True,
                       copy=False, tracking=True)
    diseases_ids = fields.Many2many('hms.diseases', 'diseases_prescription_rel', 'diseas_id', 'prescription_id',
                                    string='Diseases', states=READONLY_STATES, tracking=True)
    group_id = fields.Many2one('medicament.group', ondelete="set null", string='Medicaments Group',
                               states=READONLY_STATES, copy=False)

    advice_id = fields.Many2many('advice.template', 'advice_prescription_rel', 'advice_id', 'prescription_id',
                                 string='Advice Template', states=READONLY_STATES, copy=False)

    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', required=True,
                                 states=READONLY_STATES, tracking=True)
    pregnancy_warning = fields.Boolean(string='Pregnancy Warning', states=READONLY_STATES)
    notes = fields.Html(string='Notes', states=READONLY_STATES)
    prescription_line_ids = fields.One2many(comodel_name='prescription.line', inverse_name='prescription_id',
                                            string='Prescription line',
                                            states=READONLY_STATES, copy=True, auto_join=True, tracking=True)
    prescription_detail_ids = fields.One2many(comodel_name='prescription.detail', inverse_name='prescription_id',
                                              string='Prescription detail',
                                              copy=False, auto_join=True)
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Clinic',
                                 default=lambda self: self.env.user.company_id, states=READONLY_STATES)
    prescription_date = fields.Datetime(string='Prescription Date', required=True, default=fields.Datetime.now,
                                        states=READONLY_STATES, tracking=True, copy=False)
    prescription_date_format = fields.Char(string='Prescription Date Format',
                                           compute='_compute_prescription_date_format')
    physician_id = fields.Many2one('hms.physician', ondelete="restrict", string='Prescriber',
                                   states=READONLY_STATES, default=_current_user_doctor, tracking=True)
    physician_phone = fields.Char('Phone')
    state = fields.Selection([
        ('draft', 'Prescription Order'),
        ('confirmed', 'Pending Review'),
        ('prescription', 'Prescribed'),
        ('request', 'Request Change'),
        ('finished', 'Completed'),
        ('canceled', 'Cancelled'),
        ('expired', 'Expired')], string='Status', default='draft', tracking=True)

    appointment_ids = fields.One2many('hms.appointment', 'prescription_id', string='Appointments',
                                      states=READONLY_STATES)

    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict",
                                     string='Appointment', states=READONLY_STATES)
    patient_age = fields.Char(related='patient_id.age', string='Age', store=True, readonly=True)
    treatment_id = fields.Many2one('hms.treatment', 'Treatment', states=READONLY_STATES)
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'prescription_medical_alert_rel', 'prescription_id',
                                         'alert_id',
                                         string='Medical Alerts', related="patient_id.medical_alert_ids")
    alert_count = fields.Integer(compute='_get_alert_count', default=0)
    old_prescription_id = fields.Many2one('prescription.order', 'Old Prescription', copy=False, states=READONLY_STATES)
    acs_kit_id = fields.Many2one('acs.product.kit', string='Template', states=READONLY_STATES)
    medicament_group_id = fields.Many2many('medicament.group', 'prescription_medical_group_rel', 'prescription_id',
                                           'group_id', string='Template', states=READONLY_STATES)
    acs_kit_qty = fields.Integer("Kit Qty", states=READONLY_STATES, default=1)
    expire_date = fields.Date(
        string='Expire Date',
        default=lambda x: fields.Date.today() + relativedelta(years=1),
        states=READONLY_STATES)
    prescription_type = fields.Selection([
        ("botox", "Botox Injections"),
        ("filler", "Dermal Fillers"),
        ("laser_hair_removal", "Laser Hair Removal"),
        ("chemical_peels", "Chemical Peels"),
        ("microdermabrasion", "Microdermabrasion"),
        ("lip_fillers", "Lip Fillers"),
        ("other", "Other"),
    ],
        string='Procedure', default='other',
        states=READONLY_STATES,
        required=True, tracking=True)

    first_product_id = fields.Many2one('product.product', string="Medicine", compute='get_1st_product')
    nurse_id = fields.Many2one('res.users', 'Clinician', domain=[('physician_id', '=', False)], required=True,
                               default=_get_clinician, states=READONLY_STATES, )

    survey_answer_ids = fields.One2many('survey.user_input.line', 'prescription_id', 'Answer',
                                        copy=False, readonly=True)

    is_editable = fields.Boolean("Is Editable", compute='_compute_is_editable')
    is_locked = fields.Boolean("Is Locked", compute='_compute_is_locked')
    is_doctor_editable = fields.Boolean("Is Doctor Editable", default=True, readonly=1)
    is_prescriber_fee = fields.Boolean('Is Prescriber fee', default=True, states=READONLY_STATES, )
    prescriber_fee = fields.Float('Prescriber fee', default=25.0, states=READONLY_STATES)
    transaction_ids = fields.One2many('payment.transaction', 'prescription_id', string='Payment Transaction',
                                      readonly=1)
    transaction_count = fields.Integer(compute='_rec_count', string='Transactions')
    product_ids = fields.Many2many('product.product', compute='_compute_product_ids', string='Medicines')
    product_name = fields.Char(compute='_compute_product_ids', string='Medicine Name')
    product_area = fields.Html(compute='_compute_product_ids', string='Medicine Area')
    treatment_ids = fields.Many2many('hms.treatment', 'prescription_treatment_rel', 'treatment_id', 'prescription_id')
    treatment_medicine_count = fields.Integer(compute='_rec_count', string='History')
    is_owner_prescriber = fields.Boolean("Owner Prescriber", compute='_compute_is_owner_prescriber', store=True)
    department_id = fields.Many2one('hr.department', domain=[('patient_department', '=', True)], default=get_clinic,
                                    string='Clinic Name', tracking=True)

    pharmacy_product_id = fields.Many2one('product.product', ondelete="cascade", string='Pharmacy Product',
                                          domain=[('hospital_product_type', '=', 'pharmacy')],
                                          tracking=True)

    treatment_id = fields.Many2one('hms.treatment', ondelete="restrict",
                                   string='Treatment')

    def write(self, vals):
        res = super(ACSPrescriptionOrder, self).write(vals)

        return res

    def action_save_and_close(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('prescription_line_ids', 'prescription_line_ids.product_id')
    def _compute_product_ids(self):
        for rec in self:
            tmp = ''
            rec.product_ids = False
            rec.product_ids = rec.prescription_line_ids.mapped('product_id')
            rec.product_name = ''
            rec.product_area = ''

            for line in rec.prescription_line_ids:
                rec.product_name += str(line.product_id.name)
                dose = ''
                area = ''
                if line.medicine_area_id:
                    area = line.medicine_area_id.name
                if line.medicine_amount:
                    dose = line.medicine_amount.name
                tmp += str(line.product_id.name) + ' ' + area + ' ' + str(dose) + '<br/>'
            rec.product_area = tmp

    @api.depends('prescription_date')
    def _compute_prescription_date_format(self):
        for rec in self:
            rec.prescription_date_format = ''
            if rec.prescription_date:
                rec.prescription_date_format = rec.prescription_date.strftime('%Y-%m-%d %H:%M')

    def _compute_is_editable(self):
        is_nurse = self.env.user.has_group('acs_hms_base.group_hms_manager')
        for record in self:
            record.is_editable = True
            if is_nurse and not self.env.is_admin():
                record.is_editable = False

    @api.depends('prescription_date', 'state')
    def _compute_is_locked(self):
        for record in self:
            record.is_locked = False
            if record.state == 'prescription':
                now = datetime.now()
                timedelta_cal = datetime.strptime(now.strftime('%Y-%m-%d %H:%M:%S'),
                                                  '%Y-%m-%d %H:%M:%S') - record.prescription_date
                hours, remainder = divmod(timedelta_cal.seconds, 3600)
                days_to_hours = timedelta_cal.days * 24
                remainder = remainder // 60
                remainder = round(remainder / 60, 2)
                hour = hours + days_to_hours + remainder
                if hour > 24:
                    record.is_locked = True
                    record.is_doctor_editable = True

    def cron_check_prescription_locked(self):
        pres = self.env['prescription.order'].search([('state', '=', 'prescription')])
        for record in pres:
            record.is_locked = False
            now = datetime.now()
            timedelta_cal = datetime.strptime(now.strftime('%Y-%m-%d %H:%M:%S'),
                                              '%Y-%m-%d %H:%M:%S') - record.prescription_date
            hours, remainder = divmod(timedelta_cal.seconds, 3600)
            days_to_hours = timedelta_cal.days * 24
            remainder = remainder // 60
            remainder = round(remainder / 60, 2)
            hour = hours + days_to_hours + remainder
            if hour > 24:
                record.is_locked = True
                record.is_doctor_editable = True
        return True

    @api.depends('physician_id')
    def _compute_is_owner_prescriber(self):
        is_doctor = self.env.user.has_group('acs_hms.group_hms_doctor')
        for record in self:
            record.is_owner_prescriber = False
            if is_doctor and record.physician_id.user_id.id == self.env.user.id:
                record.is_owner_prescriber = True
                record.is_prescriber_fee = False
                record.prescriber_fee = 0.0

    def get_1st_product(self):
        for rec in self:
            if rec.prescription_line_ids:
                if rec.prescription_line_ids[0].product_id:
                    rec.first_product_id = rec.prescription_line_ids[0].product_id
                else:
                    rec.first_product_id = False
            else:
                rec.first_product_id = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.unique_code = uuid.uuid4()
        return res

    @api.onchange('group_id')
    def on_change_group_id(self):
        product_lines = []
        for rec in self:
            appointment_id = rec.appointment_id and rec.appointment_id.id or False
            for line in rec.group_id.medicament_group_line_ids:
                product_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'common_dosage_id': line.common_dosage_id and line.common_dosage_id.id or False,
                    'dose': line.dose,
                    'dosage_uom_id': line.dosage_uom_id,
                    'active_component_ids': [(6, 0, [x.id for x in line.product_id.active_component_ids])],
                    'form_id': line.product_id.form_id.id,
                    'qty_per_day': line.dose,
                    'days': line.days,
                    'name': line.reason,
                    'allow_substitution': line.allow_substitution,
                    'appointment_id': appointment_id,
                }))
            rec.prescription_line_ids = product_lines

    @api.onchange('appointment_id')
    def onchange_appointment(self):
        if self.appointment_id and self.appointment_id.treatment_id:
            self.treatment_id = self.appointment_id.treatment_id.id

    @api.onchange('advice_id')
    def onchange_advice_id(self):
        self.notes = ''
        if self.advice_id:
            for advice in self.advice_id:
                self.notes += advice.description or ''

    @api.onchange('physician_id')
    def onchange_physician_id(self):
        if self.physician_id:
            self.physician_phone = self.physician_id.phone or self.physician_id.mobile

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft', 'confirmed']:
                raise UserError(_('Prescription Order can be delete only in Draft state.'))
        return super(ACSPrescriptionOrder, self).unlink()

    def button_cancel(self):
        self.prescription_detail_ids.write({'state': 'cancel'})
        self.write({'state': 'canceled'})

    def button_reset(self):
        self.prescription_detail_ids.unlink()
        self.write({'state': 'draft'})

    def button_approve_request(self):
        for record in self:
            template_id = self.env.ref('acs_hms.acs_prescription_approve_request_email')
            template_id.sudo().send_mail(record.id, raise_exception=False, force_send=True)
            record.write({'state': 'prescription'})

    def button_reject_request(self):
        self.write({'state': 'request'})

    def button_edit(self):
        self.is_doctor_editable = False

    def button_open_edit(self):
        if not self.is_locked:
            self.is_doctor_editable = False
        return {
            'name': f"Prescription",
            'view_mode': 'form',
            'res_model': 'prescription.order',
            'view_id': self.env.ref('acs_hms.view_hms_prescription_order_form').id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'target': 'current',
            'context': {}
        }

    def call_prescriber(self):
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        url = config_parameter_obj.get_param('web.base.url')
        channel = self.env['mail.channel'].channel_get([self.physician_id.partner_id.id])
        channel_id = self.env['mail.channel'].browse(channel["id"])
        return {
            'type': 'ir.actions.act_url',
            'url': url + '/web#action=120&menu_id=82&cids=1&active_id=mail.channel_{id}'.format(id=channel_id.id),
            'target': 'self',
        }

    def button_request_change(self):
        # MailMessage.create(message_vals)
        for app in self:
            if app.physician_id:
                config_parameter_obj = self.env['ir.config_parameter'].sudo()
                url = config_parameter_obj.get_param('web.base.url')
                url += '/web#id={id}&cids=1&model=prescription.order&view_type=form'.format(id=app.id)
                body_html = '''
                            <div style="padding:0px;margin:auto;background: #FFFFFF repeat top /100%;color:#777777">
                              <p>Hi {doctor},is requesting a change to <strong>{number}</strong></p>
                              <p>URL: {url}</p>
                            </div>
                            '''.format(doctor=app.physician_id.name, number=app.name, url=url)
                channel = self.env['mail.channel'].channel_get([app.physician_id.partner_id.id])
                channel_id = self.env['mail.channel'].browse(channel["id"])
                channel_id.message_post(
                    body=(body_html),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
                app.state = 'request'
        return True

    def _prepare_invoice(self, move_type):
        self.ensure_one()
        vals = []
        service = self.env['product.product'].search([('product_tmpl_id.name', '=', 'Prescriber Service')], limit=1)
        if service:
            vals.append({
                'move_type': move_type,
                'narration': self.notes,
                'currency_id': self.env.user.company_id.currency_id.id,
                'partner_id': self.patient_id.partner_id.id if move_type == 'out_invoice' else self.physician_id.partner_id.id,
                'patient_id': self.patient_id.id,  # if move_type == 'out_invoice' else False,
                'partner_shipping_id': self.patient_id.partner_id.id if move_type == 'out_invoice' else self.physician_id.partner_id.id,
                'invoice_origin': self.name,
                'company_id': self.env.user.company_id.id,
                'invoice_date': self.prescription_date,
                'ref': self.name,
                'invoice_line_ids': [[0, 0, {
                    'product_id': service.id,
                    'quantity': 1,
                    'price_unit': service.list_price if move_type == 'out_invoice' else service.standard_price,
                    'name': service.name or self.name,
                    'product_uom_id': service.uom_id.id}]]

            })
        return vals

    def pay_confirm(self):
        for app in self:
            if not app.physician_id:
                raise UserError(_('You cannot confirm a prescription order without Prescriber.'))
            if not app.prescription_line_ids:
                raise UserError(_('You cannot confirm a prescription order without any order line.'))
            if not app.is_owner_prescriber:
                action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_pay_prescriber_wiz")
                # action['domain'] = [('patient_id', '=', self.id)]
                action['context'] = {'show_pop_up': False}
                action['res_model'] = 'pay.prescriber.wiz'
                return action
            elif app.is_owner_prescriber:
                app.state = 'confirmed'

    def confirm_without_pay(self):
        for app in self:
            if not app.name:
                prescription_type_label = app._fields['prescription_type'].selection
                prescription_type_label = dict(prescription_type_label)
                # prescription_type_label.get(app.prescription_type) + ": " +
                app.name = self.env['ir.sequence'].next_by_code('prescription.order') or '/'
            app.state = 'confirmed'

    def pay_prescription(self):
        self.button_confirm()

    def button_confirm(self):
        for app in self:
            if not app.prescription_line_ids:
                raise UserError(_('You cannot confirm a prescription order without any order line.'))

            app.state = 'confirmed'
            if not app.name:
                prescription_type_label = app._fields['prescription_type'].selection
                prescription_type_label = dict(prescription_type_label)
                # prescription_type_label.get(app.prescription_type) + ": " +
                app.name = self.env['ir.sequence'].next_by_code('prescription.order') or '/'
            invoice_vals = self._prepare_invoice(move_type='out_invoice')
            moves = self.env['account.move'].sudo().create(invoice_vals)
            if moves:
                moves.action_post()

    def action_view_transaction(self):
        action = self.env["ir.actions.actions"]._for_xml_id("payment.action_payment_transaction")
        transaction_ids = self.env['payment.transaction'].search(
            [('reference', '=', self.name), ('partner_id', '=', self.env.user.partner_id.id)])
        action['domain'] = [('id', 'in', transaction_ids.ids)]
        action['views'] = [(self.env.ref('payment.payment_transaction_list').id, 'tree'),
                           (self.env.ref('payment.payment_transaction_form').id, 'form')]
        return action

    def action_view_medicine_history(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.acs_action_form_hospital_treatment")
        history_ids = self.env['hms.treatment'].search(
            [('patient_id', '=', self.patient_id.id)])
        action['domain'] = [('id', 'in', history_ids.ids)]
        action['search_view_id'] = self.env.ref('acs_hms.view_hms_treatment_search').id
        action['context'] = {'search_default_patient_groupby': 1, 'search_patient_groupby': 1}
        # action['views'] = [(self.env.ref('acs_hms.act_open_hms_medicine_line_view').id, 'tree'), (False, 'form')]
        return action

    def action_view_medical_checklist(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_tree_patient_medical_checklist")
        history_ids = self.env['patient.medical.checklist.line'].search(
            [('patient_id', '=', self.patient_id.id)])
        action['domain'] = [('id', 'in', history_ids.ids)]
        return action

    def button_prescribe_confirm(self):
        for app in self:
            if not app.name:
                app.name = self.env['ir.sequence'].next_by_code('prescription.order') or '/'
            app.state = 'prescription'
            invoice_vals = self._prepare_invoice(move_type='in_invoice')
            moves = self.env['account.move'].sudo().create(invoice_vals)
            if moves:
                moves.action_post()
            # create prescription detail based on prescription line
            vals_list = []
            for line in app.prescription_line_ids:
                if line.product_id and line.repeat > 0:
                    for i in range(line.repeat):
                        vals = {
                            'name': line.product_id.name,
                            'description': line.product_id.description or '',
                            'prescription_id': app.id,
                            'line_id': line.id,
                            'product_id': line.product_id.id,
                            'scheduled_date':
                                app.prescription_date.date() + relativedelta(months=i * line.use_every),
                        }
                        vals_list.append(vals)
            if len(vals_list) > 0:
                self.env['prescription.detail'].create(vals_list)

            MailMessage = self.env['mail.message']
            appointment = False
            physician = False
            if app.appointment_id:
                appointment = app.appointment_id.name
            if app.physician_id:
                physician = app.physician_id.name
            body_html = '''
                       <div style="padding:0px;margin:auto;background: #FFFFFF repeat top /100%;color:#777777">
                       <p>Hello {nurse},</p>
                       <p>Your Prescription details. For more details please refer attached PDF report.</p>
                       <ul>
                           <li>
                               <p>Reference Number: {number}</p>
                           </li>                         
                           <li>
                               <p>Prescription Date: {prescription_date}</p>
                           </li>
                       </ul>
                       <p>Please feel free to call anytime for further information or any query.</p>
                       <p>Best regards.</p><br/>
                   </div>
                   '''.format(nurse=app.nurse_id.name, number=app.name, prescription_date=app.prescription_date)
            message_vals = {
                'res_id': app.id,
                'model': app._name,
                'message_type': 'notification',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'body': body_html
            }
            # MailMessage.create(message_vals)
            channel = self.env['mail.channel'].channel_get([app.nurse_id.partner_id.id])
            channel_id = self.env['mail.channel'].browse(channel["id"])
            pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'acs_hms.report_hms_prescription_id', res_ids=[app.id])
            att_name = app.name if app.name else ''
            attachment = self.env['ir.attachment'].create({
                'name': 'prescription_' + att_name,
                'type': 'binary',
                'raw': pdf_content,
                'res_model': app._name,
                'res_id': app.id
            })
            channel_id.message_post(
                body=(body_html),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                attachment_ids=[attachment.id]
            )
            # template_id = self.env.ref('acs_hms.acs_prescription_email')
            # template_id.sudo().send_mail(app.id, raise_exception=False, force_send=True)
            # channel = self.env['mail.channel'].create(message_vals)

    def button_done(self):
        for app in self:
            app.state = 'finished'

    def print_report(self):
        return self.env.ref('acs_hms.report_hms_prescription_id').report_action(self)

    @api.onchange('patient_id')
    def onchange_patient(self):
        if self.patient_id:
            prescription = self.search([('patient_id', '=', self.patient_id.id), ('state', '=', 'prescription')],
                                       order='id desc', limit=1)
            self.old_prescription_id = prescription.id if prescription else False
            # self.physician_id = self.patient_id.primary_physician_id.id if self.patient_id.primary_physician_id else False

    @api.onchange('pregnancy_warning')
    def onchange_pregnancy_warning(self):
        if self.pregnancy_warning:
            warning = {}
            message = ''
            for line in self.prescription_line_ids:
                if line.product_id.pregnancy_warning:
                    message += _("%s Medicine is not Suggastable for Pregnancy.") % line.product_id.name
                    if line.product_id.pregnancy:
                        message += ' ' + line.product_id.pregnancy + '\n'

            if message:
                return {
                    'warning': {
                        'title': _('Pregnancy Warning'),
                        'message': message,
                    }
                }

    def get_prescription_lines(self):
        appointment_id = self.appointment_id and self.appointment_id.id or False
        product_lines = []
        for line in self.old_prescription_id.prescription_line_ids:
            product_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'common_dosage_id': line.common_dosage_id and line.common_dosage_id.id or False,
                'dose': line.dose,
                'active_component_ids': [(6, 0, [x.id for x in line.active_component_ids])],
                'form_id': line.form_id.id,
                'qty_per_day': line.qty_per_day,
                'days': line.days,
                'name': line.name,
                'allow_substitution': line.allow_substitution,
                'appointment_id': appointment_id,
            }))
        self.prescription_line_ids = product_lines

    """
    Retrieves the ACS kit lines associated with the current instance of the class.

    Returns:
        list: A list of tuples representing the ACS kit lines. Each tuple contains the following elements:
            - int: The ID of the product.
            - int: The ID of the common dosage.
            - float: The dosage of the product.
            - list: A list of IDs representing the active components of the product.
            - int: The ID of the form.
            - int: The quantity per day.
            - int: The number of days.
            - int: The appointment ID.

    Raises:
        UserError: If the ACS kit ID is not set.
    """

    @api.onchange('acs_kit_id')
    def get_acs_kit_lines(self):
        # self.notes = self.acs_kit_id.description
        lines = []
        appointment_id = self.appointment_id and self.appointment_id.id or False
        self.prescription_line_ids = False
        if self.acs_kit_id:
            for line in self.acs_kit_id.acs_kit_line_ids:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'common_dosage_group': line.dosage or False,
                    'dose': line.product_id.dosage,
                    'active_component_ids': [(6, 0, [x.id for x in line.product_id.active_component_ids])],
                    'form_id': line.product_id.form_id.id,
                    'qty_per_day': line.product_id.common_dosage_id and line.product_id.common_dosage_id.qty_per_day or 1,
                    'days': line.product_id.common_dosage_id and line.product_id.common_dosage_id.days or 1,
                    'appointment_id': appointment_id,
                    'name': appointment_id,
                }))
        self.prescription_line_ids = lines

    @api.onchange('medicament_group_id')
    def get_acs_medicament_group(self):
        # self.notes = self.acs_kit_id.description
        lines = []
        appointment_id = self.appointment_id and self.appointment_id.id or False
        self.prescription_line_ids = False
        if self.medicament_group_id:
            for group in self.medicament_group_id:
                for line in group.medicament_group_line_ids:
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'medicine_area_id': line.medicine_area_id.id or False,
                        'medicine_technique_id': line.medicine_technique_id.id or False,
                        'medicine_depth_id': line.medicine_depth_id.id or False,
                        'medicine_method_id': line.medicine_method_id.id or False,
                        'use': line.use,
                        'repeat': line.repeat,
                        'common_dosage_group': line.common_dosage_id.id or False,
                        'dose': line.dose or line.product_id.dosage,
                        'allow_substitution': line.allow_substitution,
                        'dosage_uom_id': line.dosage_uom_id.id if line.common_dosage_id else False,
                        'active_component_ids': [(6, 0, [x.id for x in line.product_id.active_component_ids])],
                        'form_id': line.product_id.form_id.id,
                        'qty_per_day': line.qty_per_day or line.product_id.common_dosage_id and line.product_id.common_dosage_id.qty_per_day or 1,
                        'days': line.days or line.product_id.common_dosage_id and line.product_id.common_dosage_id.days or 1,
                        'appointment_id': appointment_id,
                        'name': appointment_id,
                    }))
        self.prescription_line_ids = lines

    def action_prescription_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id('acs_hms.acs_prescription_email',
                                                                 raise_if_not_found=False)
        ctx = {
            'default_model': 'prescription.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def make_appointment(self):
        return {
            'name': f"Appointment",
            'view_mode': 'form',
            'res_model': 'hms.appointment',
            'view_id': self.env.ref('acs_hms.view_hms_appointment_form').id,
            'res_id': False,
            'type': 'ir.actions.act_window',
            # 'target': 'new',
            'context': {'default_patient_id': self.patient_id.id,
                        'default_consutation_type': 'followup',
                        'default_prescription_id': self.id,
                        }
        }

    def acs_select_prescription_for_appointment(self):
        if self._context.get('default_appointment_id'):
            # Check if we can get back to appointment in breadcrumb.
            appointment = self.env['hms.appointment'].search(
                [('id', '=', self._context.get('default_appointment_id'))])
            appointment.prescription_id = self.id
            action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
            action['res_id'] = appointment.id
            action['context'] = {'autofocus': 'autofocus'}
            action['views'] = [(self.env.ref('acs_hms.view_hms_appointment_form').id, 'form')]

            return action
        else:
            raise UserError(_("Something went wrong! Please Open Appointment and try again"))

    def select_prescription(self):
        self.ensure_one()
        # get current treatment
        treatment = self.env.context.get('default_treatment_id', False)
        if not treatment:
            raise UserError(_("Treatment not found!"))
        # self.treatment_ids = [(4, treatment)]
        treatment = self.env['hms.treatment'].browse(treatment)
        treatment.prescription_ids = [(4, self.id)]
        treatment.onchange_prescription_ids()

    def remove_prescription(self):
        self.ensure_one()
        # get current treatment
        treatment = self.env.context.get('default_treatment_id', False)
        if not treatment:
            raise UserError(_("Treatment not found!"))
        treatment = self.env['hms.treatment'].browse(treatment)
        treatment.prescription_ids = [(3, self.id)]
        treatment.onchange_prescription_ids()


class ACSPrescriptionLine(models.Model):
    _name = 'prescription.line'
    _description = "Prescription Order Line"
    _order = "sequence"

    @api.depends('qty_per_day', 'days', 'dose', 'manual_quantity', 'manual_prescription_qty', 'state')
    def _get_total_qty(self):
        for rec in self:
            if rec.manual_prescription_qty:
                rec.quantity = rec.manual_quantity
            else:
                rec.quantity = rec.days * rec.qty_per_day * rec.dose

    name = fields.Char(string='Description', help='Short comment on the specific drug')
    sequence = fields.Integer("Sequence", default=10)
    prescription_id = fields.Many2one('prescription.order', ondelete="cascade", string='Prescription')
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Product',
                                 domain=[('hospital_product_type', '=', 'medicament'), ('qty_available', '>', 0)],
                                 tracking=True)
    allow_substitution = fields.Boolean(string='Allow Substitution')
    prnt = fields.Boolean(string='Print', help='Check this box to print this line of the prescription.', default=True)
    manual_prescription_qty = fields.Boolean(related="product_id.manual_prescription_qty",
                                             string="Enter Prescription Qty Manually.", store=True)
    quantity = fields.Float(string='Units', compute="_get_total_qty", inverse='_inverse_total_qty', compute_sudo=True,
                            store=True, help="Number of units of the medicament. Example : 30 capsules of amoxicillin",
                            default=1.0)
    manual_quantity = fields.Float(string='Manual Total Qty', default=1)
    active_component_ids = fields.Many2many('active.comp', 'product_pres_comp_rel', 'product_id', 'pres_id',
                                            'Active Component')
    dose = fields.Integer('Dosage', help="Amount of medication (eg, 250 mg) per dose", default=1, tracking=True)
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')
    dosage_uom_id = fields.Many2one('uom.uom', string='Unit of Dosage', help='Amount of Medicine (eg, mg) per dose',
                                    domain="[('category_id', '=', product_uom_category_id)]")
    form_id = fields.Many2one('drug.form', related='product_id.form_id', string='Form',
                              help='Drug form, such as tablet or gel')
    route_id = fields.Many2one('drug.route', ondelete="cascade", string='Route',
                               help='Drug form, such as tablet or gel')
    common_dosage_id = fields.Many2one('medicament.dosage', ondelete="cascade", string='Dosage/Frequency',
                                       help='Drug form, such as tablet or gel')
    common_dosage_group = fields.Char(string='Dosage/Frequency', help='Drug form, such as tablet or gel')
    short_comment = fields.Char(string='Comment', help='Short comment on the specific drug')
    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict", string='Appointment')
    treatment_id = fields.Many2one('hms.treatment', related='prescription_id.treatment_id', string='Treatment',
                                   store=True)
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Clinic',
                                 related='prescription_id.company_id')
    qty_available = fields.Float(compute='_compute_colour_forecast', string='Available Qty',
                                 digits='Product Unit of Measure', compute_sudo=True)
    days = fields.Float("Days", default=1.0)
    qty_per_day = fields.Float(string='Qty Per Day', default=1.0)
    state = fields.Selection(related="prescription_id.state", store=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], help="Technical field for UX purpose.")
    repeat = fields.Integer(string='Repeat', default=5)
    # remain_repeat = fields.Integer(string='Remaining Repeat', compute='_compute_remaining_repeat')
    use_every = fields.Integer(
        "Use Every (months)", default=1,
        help="This field used to schedule \
            the email notify the customer \
            to schedule the appointment")
    use = fields.Selection([('Stat', 'Stat'), ('3', '3 months'), ('6', '6 months'), ('12', '12 months')],
                           string="Expiration", help="")
    is_red = fields.Boolean(default=False)
    colour_forecast = fields.Char(string="Color", compute='_compute_colour_forecast')

    is_pbs = fields.Boolean('PBS', default=False)

    medicine_area_id = fields.Many2one('medicine.area', string="Area")
    medicine_technique_id = fields.Many2one('medicine.technique', string='Technique')
    medicine_depth_id = fields.Many2one('medicine.depth', string='Depth')
    medicine_method_id = fields.Many2one('medicine.method', string='Method')
    medicine_amount = fields.Many2one('medicine.amount', string='Dose')

    acs_lot_id = fields.Many2one("stock.lot",
                                 domain="[('product_id', '=', product_id),'|',('expiration_date','=',False),"
                                        "('expiration_date', '>', context_today().strftime('%Y-%m-%d'))]",
                                 string="Lot/Serial number")

    @api.depends('product_id', 'acs_lot_id', 'qty_available', 'dose')
    def _compute_colour_forecast(self):
        for line in self:
            line.is_red = False
            line.colour_forecast = "#008000"
            line.qty_available = line.product_id.qty_available
            if line.acs_lot_id:
                line.qty_available = line.acs_lot_id.product_qty
            if line.qty_available < float(line.dose):
                line.is_red = True
                line.colour_forecast = "#FF0000"

    @api.depends('repeat')
    def _compute_remaining_repeat(self):
        for rec in self:
            repeat_used = len(self.env['hms.appointment'].search([
                ('prescription_id', '=', rec.prescription_id.id),
                ('state', 'in', ['to_after_care', 'done'])]))
            rec.remain_repeat = rec.repeat - repeat_used if rec.repeat > repeat_used else 0

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.active_component_ids = [(6, 0, [x.id for x in self.product_id.active_component_ids])]
            self.form_id = self.product_id.form_id and self.product_id.form_id.id or False,
            self.route_id = self.product_id.route_id and self.product_id.route_id.id or False,
            self.dosage_uom_id = self.product_id.dosage_uom_id and self.product_id.dosage_uom_id.id or self.product_id.uom_id.id,
            self.quantity = 1
            self.dose = self.product_id.dosage or 1
            self.repeat = 5
            self.allow_substitution = self.product_id.acs_allow_substitution
            self.common_dosage_id = self.product_id.common_dosage_id and self.product_id.common_dosage_id.id or False
            # self.name = self.product_id.display_name

            if self.prescription_id and self.prescription_id.pregnancy_warning:
                warning = {}
                message = ''
                if self.product_id.pregnancy_warning:
                    message = _("%s Medicine is not Suggastable for Pregnancy.") % self.product_id.name
                    if self.product_id.pregnancy:
                        message += ' ' + self.product_id.pregnancy
                    warning = {
                        'title': _('Pregnancy Warning'),
                        'message': message,
                    }

                if warning:
                    return {'warning': warning}

            return {'domain': {'acs_lot_id': [('product_id', '=', self.product_id.id), '|',
                                              ('expiration_date', '=', False),
                                              ('expiration_date', '>', datetime.now().strftime('%Y-%m-%d'))]}}

    @api.onchange('common_dosage_id')
    def onchange_common_dosage(self):
        if self.common_dosage_id:
            self.qty_per_day = self.common_dosage_id.qty_per_day or 1
            self.days = self.common_dosage_id.days or 1

    @api.onchange('quantity')
    def _inverse_total_qty(self):
        for line in self:
            if line.product_id.manual_prescription_qty:
                line.manual_quantity = line.quantity
            else:
                line.manual_quantity = 0.0


class AdviceTemplate(models.Model):
    _name = "advice.template"
    _description = "Advice Template"
    _rec_name = 'name'

    name = fields.Char(string='Title', required=True)
    description = fields.Html(string='Advice', required=True)


class PrescriptionDetail(models.Model):
    _name = "prescription.detail"
    _description = "Prescription Details"
    _order = "scheduled_date"

    name = fields.Char(string='Title', required=True)
    description = fields.Html(string='Advice', required=True)
    sequence = fields.Integer("Sequence", default=10)
    prescription_id = fields.Many2one('prescription.order', ondelete="cascade", string='Prescription')
    line_id = fields.Many2one('prescription.line', ondelete="cascade", string='Prescription Line')
    product_id = fields.Many2one('product.product', required=True, ondelete="cascade", string='Product')
    scheduled_date = fields.Date(string='Scheduled Date')
    state = fields.Selection([
        ('schedule', 'Scheduled'),
        ('sent', 'Email Sent'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], store=True, required=True,
        default='schedule', string='Status', tracking=True)
    is_done = fields.Boolean(string='Done')
    done_at = fields.Datetime("Done at")

    @api.model
    def send_prescription_reminder(self):
        """
        This function is used to send the prescription reminder
        """
        today = fields.Date.today()

        # update status if prescription is expired
        _logger = logging.getLogger(__name__)
        expired_prescription_ids = self.env['prescription.order'].search(
            [('expire_date', '<=', today),
             ('state', '!=', 'expired')])
        if expired_prescription_ids:
            for pre in expired_prescription_ids:
                print("pre", pre.name)
                pre.write({'state': 'expired'})
                logging.info(f"Updated {pre.name} expired prescription")
        else:
            logging.info(f"There is not any expired prescription")

        prescription_ids = self.search(
            [('scheduled_date', '<=', today + relativedelta(weeks=1)), ('state', '=', 'schedule')])
        # use a hack here to avoid sending multiple email to the same patient
        patient_ids = {}
        for rec in prescription_ids:
            if rec.prescription_id.patient_id not in patient_ids:
                patient_ids[rec.prescription_id.patient_id] = rec
            else:
                patient_ids[rec.prescription_id.patient_id] += rec
        for key, value in patient_ids.items():
            if value:
                value[0].send_prescription_reminder_mail(ids=value.ids)
                value.write({'state': 'sent'})

    def send_prescription_reminder_mail(self, ids=False):
        """
        This function is used to send the prescription reminder mail
        """
        template_id = self.env.ref('acs_hms.email_template_prescription_reminder')
        template_id.with_context(lines=ids).send_mail(res_id=self.id, email_values={
            'email_from': self.env.user.with_user(SUPERUSER_ID).email_formatted})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import odoo
import logging

_logger = logging.getLogger(__name__)


class AppointmentPurpose(models.Model):
    _name = 'appointment.purpose'
    _description = "Appointment Purpose"

    name = fields.Char(string='Appointment Purpose', required=True, translate=True)


class AppointmentCabin(models.Model):
    _name = 'appointment.cabin'
    _description = "Appointment Cabin"

    name = fields.Char(string='Appointment Cabin', required=True, translate=True)


class AcsCancelReason(models.Model):
    _name = 'acs.cancel.reason'
    _description = "Reason"

    name = fields.Char('Reason')


class Appointment(models.Model):
    _name = 'hms.appointment'
    _description = "Appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'acs.documnt.mixin']
    _order = "id desc"

    @api.model
    def _get_service_id(self):
        consultation = False
        if self.env.user.company_id.consultation_product_id:
            consultation = self.env.user.company_id.consultation_product_id.id
        return consultation

    @api.model
    def _get_default_physician(self):
        if self.department_id:
            return self.env['hms.physician'].search([('user_id.department_ids', '=', [self.department_id.id])], limit=1)

    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)

    @api.depends('consumable_line_ids')
    def _get_consumable_line_count(self):
        for rec in self:
            rec.consumable_line_count = len(rec.consumable_line_ids)

    @api.depends('patient_id', 'patient_id.birthday', 'date')
    def get_patient_age(self):
        for rec in self:
            age = ''
            if rec.patient_id.birthday:
                end_data = rec.date or fields.Datetime.now()
                delta = relativedelta(end_data, rec.patient_id.birthday)
                if delta.years <= 2:
                    age = str(delta.years) + _(" Year") + str(delta.months) + _(" Month ") + str(delta.days) + _(
                        " Days")
                else:
                    age = str(delta.years) + _(" Year")
            rec.age = age

    @api.depends('evaluation_ids')
    def _get_evaluation(self):
        for rec in self:
            rec.evaluation_id = rec.evaluation_ids[0].id if rec.evaluation_ids else False

    def _acs_get_invoice_count(self):
        AccountMove = self.env['account.move']
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    def _acs_invoice_policy(self):
        for rec in self:
            appointment_invoice_policy = rec.sudo().company_id.appointment_invoice_policy
            if rec.product_id.appointment_invoice_policy:
                appointment_invoice_policy = rec.product_id.appointment_invoice_policy
            rec.appointment_invoice_policy = appointment_invoice_policy

    def get_procudures_to_invoice(self):
        Procedure = self.env['acs.patient.procedure']
        for rec in self:
            procedures = Procedure.search([('appointment_ids', 'in', rec.id), ('invoice_id', '=', False)])
            rec.procedure_to_invoice_ids = [(6, 0, procedures.ids)]

    def _default_survey_id(self):
        return self.env['survey.survey'].search([('title', '=', 'Medical Checklist')], limit=1)

    def acs_get_department(self):
        for rec in self:
            acs_department_id = False
            if rec.department_id and rec.department_id.id:
                acs_department_id = self.env['hr.department'].sudo().search([('id', '=', rec.department_id.id)]).id
            rec.acs_department_id = acs_department_id

    READONLY_STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}
    READONLY_CONFIRMED_STATES = {'confirm': [('readonly', True)], 'in_consultation': [('readonly', True)],
                                 'pause': [('readonly', True)], 'to_invoice': [('readonly', True)],
                                 'waiting': [('readonly', True)], 'cancel': [('readonly', True)],
                                 'done': [('readonly', True)]}

    REQUIRED_STATES = {'to_after_care': [('required', True)], 'done': [('readonly', True)]}

    name = fields.Char(string='Number', readonly=True, copy=False, tracking=True, states=READONLY_STATES)
    patient_id = fields.Many2one('hms.patient', ondelete='restrict', string='Patient',
                                 index=True, help='Patient Name', states=READONLY_STATES, tracking=True)
    display_name = fields.Char(compute='_compute_display_name', string='Patient')

    image_128 = fields.Binary(related='patient_id.image_128', string='Image', readonly=True)
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', default=_get_default_physician,
                                   string='Prescriber',
                                   index=True, help='', states=READONLY_STATES, tracking=True)

    def get_clinic(self):
        clinic = self.env.user.department_ids[0].id if self.env.user.department_ids else False
        return clinic

    department_id = fields.Many2one('hr.department', ondelete='restrict',
                                    domain=[('patient_department', '=', True)], string='Clinic', tracking=True,
                                    default=get_clinic,
                                    states=READONLY_STATES)

    # ACS: Added department field agian here to avoid portal error. Insted of reading department_id used acs_department_idfield so error vanbe avoided.
    acs_department_id = fields.Many2one('hr.department', compute="acs_get_department")
    invoice_exempt = fields.Boolean(string='Invoice Exempt', states=READONLY_STATES)
    follow_date = fields.Datetime(string="Follow Up Date", states=READONLY_STATES, copy=False)

    reminder_date = fields.Datetime(string="Reminder Date", states=READONLY_STATES, copy=False)
    acs_reminder_sent = fields.Boolean("Reminder Sent", default=False)

    evaluation_ids = fields.One2many('acs.patient.evaluation', 'appointment_id', 'Evaluations')
    evaluation_id = fields.Many2one('acs.patient.evaluation', ondelete='restrict', compute=_get_evaluation,
                                    string='Evaluation', states=READONLY_STATES, store=True)

    weight = fields.Float(related="evaluation_id.weight", string='Weight', help="Weight in KG", states=READONLY_STATES)
    height = fields.Float(related="evaluation_id.height", string='Height', help="Height in cm", states=READONLY_STATES)
    temp = fields.Float(related="evaluation_id.temp", string='Temp', states=READONLY_STATES)
    hr = fields.Integer(related="evaluation_id.hr", string='HR', help="Heart Rate", states=READONLY_STATES)
    rr = fields.Integer(related="evaluation_id.rr", string='RR', states=READONLY_STATES, help='Respiratory Rate')
    systolic_bp = fields.Integer(related="evaluation_id.systolic_bp", string="Systolic BP", states=READONLY_STATES)
    diastolic_bp = fields.Integer(related="evaluation_id.diastolic_bp", string="Diastolic BP", states=READONLY_STATES)
    spo2 = fields.Integer(related="evaluation_id.spo2", string='SpO2', states=READONLY_STATES,
                          help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    rbs = fields.Integer(related="evaluation_id.rbs", string='RBS', states=READONLY_STATES,
                         help="Random blood sugar measures blood glucose regardless of when you last ate.")
    bmi = fields.Float(related="evaluation_id.bmi", string='Body Mass Index')
    bmi_state = fields.Selection(related="evaluation_id.bmi_state", string='BMI State')
    acs_weight_name = fields.Char(related="evaluation_id.acs_weight_name",
                                  string='Patient Weight unit of measure label')
    acs_height_name = fields.Char(related="evaluation_id.acs_height_name",
                                  string='Patient Height unit of measure label')
    acs_temp_name = fields.Char(related="evaluation_id.acs_temp_name", string='Patient Temp unit of measure label')
    acs_spo2_name = fields.Char(related="evaluation_id.acs_spo2_name", string='Patient SpO2 unit of measure label')
    acs_rbs_name = fields.Char(related="evaluation_id.acs_rbs_name", string='Patient RBS unit of measure label')

    pain_level = fields.Selection(related="evaluation_id.pain_level", string="Pain Level")
    pain = fields.Selection(related="evaluation_id.pain", string="Pain")

    differencial_diagnosis = fields.Text(string='Differential Diagnosis', states=READONLY_STATES,
                                         help="The process of weighing the probability of one disease versus that of other diseases possibly accounting for a patient's illness.")
    medical_advice = fields.Text(string='Medical Advice', states=READONLY_STATES,
                                 help="The provision of a formal professional opinion regarding what a specific individual should or should not do to restore or preserve health.")
    chief_complain = fields.Text(string='Chief Complaints', states=READONLY_STATES,
                                 help="The concise statement describing the symptom, problem, condition, diagnosis, physician-recommended return, or other reason for a medical encounter.")
    present_illness = fields.Text(string='History of Present Illness', states=READONLY_STATES)
    lab_report = fields.Text(string='Lab Report', states=READONLY_STATES, help="Details of the lab report.")
    radiological_report = fields.Text(string='Radiological Report', states=READONLY_STATES,
                                      help="Details of the Radiological Report")
    notes = fields.Text(string='Notes', states=READONLY_STATES)
    past_history = fields.Text(string='Past History', states=READONLY_STATES, help="Past history of any diseases.")
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    payment_state = fields.Selection(related="invoice_id.payment_state", store=True, string="Payment Status")
    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('medical_emergency', 'Medical Emergency'),
    ], string='Urgency Level', default='normal', states=READONLY_STATES)
    state = fields.Selection([
        ('draft', 'Scheduled'),
        ('confirm', 'Consent'),
        ('confirm_consent', 'Medical Checklist'),
        ('waiting', 'Waiting'),
        ('in_consultation', 'Treatment'),
        ('pause', 'Pause'),
        ('to_after_care', 'AfterCare'),
        # ('to_invoice', 'Invoice'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, copy=False, tracking=True,
        states=READONLY_STATES)
    product_id = fields.Many2one('product.product', ondelete='restrict',
                                 string='Service Charge',
                                 domain=[('hospital_product_type', '=', "consultation")], required=False,
                                 states=READONLY_STATES)
    age = fields.Char(compute="get_patient_age", string='Age', store=True,
                      help="Computed patient age at the moment of the evaluation")
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    company_id = fields.Many2one('res.company', ondelete='restrict', states=READONLY_STATES,
                                 string='Hospital', default=lambda self: self.env.company)
    appointment_invoice_policy = fields.Selection([('at_end', 'Invoice in the End'),
                                                   ('anytime', 'Invoice Anytime'),
                                                   ('advance', 'Invoice in Advance')], compute=_acs_invoice_policy,
                                                  string="Appointment Invoicing Policy")
    invoice_exempt = fields.Boolean('Invoice Exempt', states=READONLY_STATES)
    consultation_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('consultation_prescription', 'Consultation and Prescription'),
        ('followup', 'Follow-Up Appointment')], 'Consultation Type', default='consultation_prescription',
        states=READONLY_STATES, copy=False)

    diseases_ids = fields.Many2many('hms.diseases', 'diseases_appointment_rel', 'diseas_id', 'appointment_id',
                                    'Diseases', states=READONLY_STATES)
    medicine_ids = fields.Many2many('product.product', 'medicines_appointment_rel', 'medicine_id', 'appointment_id',
                                    string='Medicine', domain=[('hospital_product_type', '=', 'medicament')],
                                    states=READONLY_STATES)

    medical_history = fields.Text(related='patient_id.medical_history',
                                  string="Past Medical History", readonly=True)
    patient_diseases_ids = fields.One2many('hms.patient.disease', readonly=True,
                                           related='patient_id.patient_diseases_ids', string='Disease History')

    date = fields.Datetime(string='Date', default=fields.Datetime.now, states=READONLY_CONFIRMED_STATES, tracking=True,
                           copy=False)
    date_to = fields.Datetime(string='Date To', states=READONLY_CONFIRMED_STATES, copy=False, tracking=True)
    planned_duration = fields.Float('Duration', compute="_get_planned_duration", inverse='_inverse_planned_duration',
                                    states=READONLY_CONFIRMED_STATES)
    manual_planned_duration = fields.Float('Manual Duration', states=READONLY_CONFIRMED_STATES)

    waiting_date_start = fields.Datetime('Waiting Start Date', states=READONLY_STATES, copy=False)
    waiting_date_end = fields.Datetime('Waiting end Date', states=READONLY_STATES, copy=False)
    waiting_duration = fields.Float('Wait Time', readonly=True, copy=False)
    waiting_duration_timer = fields.Float(string='Wait Timer', compute="_compute_waiting_running_duration",
                                          readonly=True, default="0.1", copy=False)

    date_start = fields.Datetime(string='Start Date', states=READONLY_STATES, copy=False)
    date_end = fields.Datetime(string='End Date', states=READONLY_STATES, copy=False)
    appointment_duration = fields.Float('Consultation Time', readonly=True, copy=False)
    appointment_duration_timer = fields.Float(string='Consultation Timer',
                                              compute="_compute_consulataion_running_duration", readonly=True,
                                              default="0.1", copy=False)

    purpose_id = fields.Many2one('appointment.purpose', ondelete='cascade',
                                 string='Purpose', help="Appointment Purpose", states=READONLY_STATES)
    cabin_id = fields.Many2one('appointment.cabin', ondelete='cascade',
                               string='Consultation Room', help="Appointment Cabin", states=READONLY_STATES,
                               copy=False)
    treatment_id = fields.Many2one('hms.treatment', ondelete='cascade',
                                   string='Treatment', help="Treatment Id", states=READONLY_STATES, tracking=True)

    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Prescriber',
                                       index=True, help='Referring Prescriber', states=READONLY_STATES,
                                       domain=[('is_referring_doctor', '=', True)])
    responsible_id = fields.Many2one('hms.physician', "Responsible Jr. Doctor", states=READONLY_STATES)
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'appointment_medical_alert_rel', 'appointment_id',
                                         'alert_id',
                                         string='Medical Alerts', related='patient_id.medical_alert_ids')
    alert_count = fields.Integer(compute='_get_alert_count', default=0)
    consumable_line_ids = fields.One2many('hms.consumable.line', 'appointment_id',
                                          string='Consumable Line', states=READONLY_STATES, copy=False)
    consumable_line_count = fields.Integer(compute="_get_consumable_line_count", store=True)
    # Only used in case of advance invoice
    consumable_invoice_id = fields.Many2one('account.move', string="Consumables Invoice", copy=False)

    pause_date_start = fields.Datetime('Pause Start Date', states=READONLY_STATES, copy=False)
    pause_date_end = fields.Datetime('Pause end Date', states=READONLY_STATES, copy=False)
    pause_duration = fields.Float('Paused Time', readonly=True, copy=False)
    prescription_ids = fields.One2many('prescription.order', 'appointment_id', 'Prescriptions', copy=False)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True,
                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                   help="If you change the pricelist, related invoice will be affected.")
    location = fields.Char(string="Appointment Location", states=READONLY_STATES)
    outside_appointment = fields.Boolean(string="Outside Appointment", states=READONLY_STATES)
    is_video_call = fields.Boolean("Is Video Call", states=READONLY_STATES)
    cancel_reason = fields.Text(string="Cancellation Reason", states=READONLY_STATES, copy=False)
    cancel_reason_id = fields.Many2one('acs.cancel.reason', string='Cancellation Reason', states=READONLY_STATES)
    user_id = fields.Many2one('res.users', string='Responsible', states=READONLY_STATES,
                              ondelete='cascade',
                              help='Responsible User for appointment validation And further Followup.')
    acs_kit_id = fields.Many2one('acs.product.kit', string='Template', states=READONLY_STATES)
    acs_kit_qty = fields.Integer("Kit Qty", states=READONLY_STATES, default=1)
    invoice_ids = fields.One2many("account.move", "appointment_id", string="Invoices",
                                  groups="account.group_account_invoice")
    invoice_count = fields.Integer(compute="_acs_get_invoice_count", string="#Invoices",
                                   groups="account.group_account_invoice")
    procedure_to_invoice_ids = fields.Many2many('acs.patient.procedure', 'acs_appointment_procedure_rel',
                                                'appointment_id', 'procedure_id', compute="get_procudures_to_invoice",
                                                string="Procedures to Invoice")
    refer_reason = fields.Text(string='Refer Reason')

    refered_from_appointment_id = fields.Many2one("hms.appointment", string="Refered From Appointment",
                                                  states=READONLY_STATES)
    refered_from_physician_id = fields.Many2one('hms.physician', related='refered_from_appointment_id.physician_id',
                                                string='Refered from Physician', states=READONLY_STATES, tracking=True,
                                                store=True)
    refered_from_reason = fields.Text(related='refered_from_appointment_id.refer_reason', string='Refered From Reason',
                                      states=READONLY_STATES, tracking=True, store=True)

    refered_to_appointment_id = fields.Many2one("hms.appointment", string="Refered Appointment", states=READONLY_STATES)
    refered_to_physician_id = fields.Many2one('hms.physician', related='refered_to_appointment_id.physician_id',
                                              ondelete='restrict', string='Refered to Physician',
                                              states=READONLY_STATES, tracking=True, store=True)

    # ACS NOTE: Because of error for portal appointment creation added _compute_field_value method.
    department_type = fields.Selection(related='department_id.department_type', string="Appointment Department",
                                       store=True)

    # Just to make object selectable in selction field this is required: Waiting Screen
    acs_show_in_wc = fields.Boolean(default=True)

    def get_current_user(self):
        return self.env.user.id or False

    def _get_pos_config(self):
        return self.env['pos.config'].search([], limit=1)

    nurse_id = fields.Many2one('res.users', 'Clinician', domain="""[('physician_id', '=', False), ('id', '=', uid)]""",
                               required=True,
                               default=get_current_user)

    prescription_id = fields.Many2one('prescription.order', 'Prescription Order')
    consent_id = fields.Many2one('consent.consent', 'Consent Form')
    is_confirmed_consent = fields.Boolean(compute='_compute_is_confirmed_consent', default=False)
    prescription_repeat = fields.Integer(compute='_compute_prescription_id', store=True, string='Prescription Repeat',
                                         readonly=True)

    consent_ids = fields.One2many(
        'consent.consent',
        'appointment_id',
        'Consent Forms',
        compute="_compute_consent_ids",
        store=True,
        readonly=False)
    is_prescription_expired = fields.Boolean(compute='_compute_is_prescription_expired')
    prescription_line_ids = fields.One2many('appointment.prescription.line', 'appointment_id', 'Prescription Line')
    prescription_line_repeat_ids = fields.One2many(related='prescription_id.prescription_line_ids')

    # attachment_ids = fields.
    attachment_before_ids = fields.Many2many('ir.attachment', 'appointment_attachment_before_rel', 'attachment_id',
                                             'appointment_id', string='Before Photos')
    attachment_after_ids = fields.Many2many('ir.attachment', 'appointment_attachment_after_rel', 'attachment_id',
                                            'appointment_id', string='After Photos')

    survey_id = fields.Many2one('survey.survey', string='Medical Checklist', default=_default_survey_id, readonly=True)

    answer_individual_ids = fields.One2many('appointment.individual.survey.answer', 'appointment_id',
                                            'Individual Checklist', readonly=True)
    answer_relevant_ids = fields.One2many('appointment.relevant.survey.answer', 'appointment_id',
                                          'Relevant Medical history', readonly=True)
    answer_medication_ids = fields.One2many('appointment.medication.survey.answer', 'appointment_id',
                                            'Medications', readonly=True)
    answer_addition_ids = fields.One2many('appointment.addition.survey.answer', 'appointment_id', 'Additional',
                                          readonly=True)

    aftercare_ids = fields.One2many(
        'patient.aftercare',
        'appointment_id',
        'Aftercare',
        states=REQUIRED_STATES,
        compute="_compute_aftercare_ids",
        store=True,
        readonly=False)

    prescription_type = fields.Selection([
        ('botox', 'Botox'),
        ('filler', 'Filler'),
        ('other', 'Other')],
        string='Procedure', default='other',
        states=READONLY_STATES,
        tracking=True)

    procedure = fields.Selection([
        # ("botox", "Botox Injections"),
        ("anti_wrinkle", "Anti Wrinkle"),
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
    procedure_ids = fields.Many2many('treatment.procedure', ondelete='restrict', string='Procedure',
                                     states=READONLY_STATES, tracking=True)

    survey_answer_ids = fields.One2many('survey.user_input.line', 'appointment_id', 'Answer',
                                        copy=False, readonly=True)

    is_done_survey = fields.Boolean('Is done survey', default=False)
    treatment_ids = fields.One2many('hms.treatment', 'appointment_id', string="Treatments")

    prescription_count = fields.Integer(compute='_rec_count', string='Prescriptions')

    is_checklist = fields.Boolean('Is checklist', compute='_compute_is_checklist')

    medical_checklist_answer_ids = fields.One2many('patient.medical.checklist.line', 'appointment_id',
                                                   string="Medical Treatment Checklist")

    duration_selection = fields.Selection([
        ("15", "15min"),
        ("30", "30min"),
        ("45", "45min"),
        ("60", "1hr"),
        ("90", "1.5hr"),
        ("120", "2hr"),
    ], string="Duration", default="30")

    is_new_patient = fields.Boolean('Is new patient', default=False)

    pos_config_id = fields.Many2one('pos.config', ondelete='cascade', default=_get_pos_config, string='POS')

    def create_patient(self):
        self.is_new_patient = True
        return {
            'name': _('New Patient'),
            'type': 'ir.actions.act_window',
            'res_model': 'hms.patient',
            'view_mode': 'form',
            'view_id': self.env.ref('acs_hms.view_patient_form').id,
            'context': {'appointment_id': self.id},
            'target': 'new',
        }

    def checkout_pos(self):
        return self.pos_config_id.open_ui()

    @api.onchange('date', 'duration_selection')
    def _onchange_duration_selection(self):
        from datetime import timedelta
        if self.date and self.duration_selection:
            self.date_to = self.date + timedelta(minutes=int(self.duration_selection))

    @api.depends('patient_id')
    def _compute_is_checklist(self):
        self.is_checklist = False
        if self.patient_id:
            for line in self.patient_id.answer_ids:
                line.appointment_id = self.id
                self.is_checklist = True

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            for line in self.patient_id.answer_ids:
                line.appointment_id = self.id

    @api.depends('procedure_ids')
    def _compute_consent_ids(self):
        for rec in self:
            if rec.procedure_ids:
                rec.consent_ids = False
                for category_id in rec.procedure_ids.category_ids:
                    # prepare consent.consent value
                    consent_val = {
                        'name': 'consent',
                        # 'procedure_id': rec.procedure_id.id,
                        'patient_id': rec.patient_id.id,
                        'nurse_id': rec.nurse_id.id,
                        'appointment_id': rec.id,
                        'knowledge_id': category_id.id,
                    }
                    rec.consent_ids = [(0, 0, consent_val)]

    @api.depends('name', 'patient_id', 'procedure_ids')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or False
            treatment = ', '.join([t.name for t in record.procedure_ids])
            if treatment:
                record.display_name = treatment
                if record.patient_id:
                    record.display_name = treatment + ' - ' + record.patient_id.name
                # if record.name:
                #     record.display_name = record.name + ' - ' + record.patient_id.name

    @api.depends(
        'treatment_ids',
        'treatment_ids.medicine_line_ids',
        'treatment_ids.medicine_line_ids.product_id',
        'treatment_ids.medicine_line_ids.product_id.aftercare_id')
    def _compute_aftercare_ids(self):
        for rec in self:
            rec.aftercare_ids = False
            product_ids = ''
            product_ids = rec.treatment_ids.mapped('medicine_line_ids.product_id')
            if not product_ids:
                continue
            aftercare_ids = False
            aftercare_ids = product_ids.mapped('aftercare_id')
            if not aftercare_ids:
                continue
            for aftercare_id in aftercare_ids:
                # prepare patient.aftercare value
                aftercare_val = {
                    'name': aftercare_id.name,
                    'knowledge_id': aftercare_id.id,
                    'appointment_id': rec.id,
                }
                rec.aftercare_ids = [(0, 0, aftercare_val)]

    def action_start_survey(self):
        self.ensure_one()
        if self.survey_id.appointment_id:
            self.survey_id.appointment_id = False
        action = self.survey_id.action_start_survey()
        # action['url'] = action['url'] + 'flag=1'
        action['context'] = {'default_appointment_id': self.id}
        action['target'] = 'new'
        self.survey_id.appointment_id = self.id
        return action

    def action_confirm_checklist(self):
        self.state = 'in_consultation'

    def action_view_aftercare(self):
        ctx = {'appointment_id': self.id, 'partner_id': self.patient_id.partner_id.id}
        return {
            'name': _('Aftercare'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'patient.aftercare',
            'views': [(False, 'tree'), (False, 'form')],
            'view_id': self.env.ref('itms_consent_form.view_aftercare_tree').id,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('prescription_id', 'prescription_id.expire_date')
    def _compute_is_prescription_expired(self):
        for rec in self:
            rec.is_prescription_expired = False
            if rec.prescription_id and rec.prescription_id.expire_date < fields.Date.today():
                rec.is_prescription_expired = True

    @api.onchange('department_id')
    def _onchange_physician_id(self):
        if self.department_id:
            self.physician_id = self.env['hms.physician'].search(
                [('user_id.department_ids', '=', [self.department_id.id])], limit=1)

    @api.onchange('prescription_id')
    def onchange_prescription_id(self):
        self.ensure_one()
        if self.prescription_id and self.is_prescription_expired:
            return {'warning':
                        {'title': _('Warning'),
                         'message': _('Prescription %s is expired!') % self.prescription_id.name}}

    @api.depends('consent_id', 'consent_id.patient_signature', 'consent_id.is_agree')
    def _compute_is_confirmed_consent(self):
        for rec in self:
            rec.is_confirmed_consent = False
            if rec.consent_id and rec.state == 'confirm':
                if rec.consent_id.patient_signature and rec.consent_id.is_agree:
                    rec.state = 'confirm_consent'
                    rec.is_confirmed_consent = True

    def update_checklist(self):
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.depends('prescription_id')
    def _compute_prescription_id(self):
        prescription_repeat = 0
        if self.prescription_id:
            for line in self.prescription_id.prescription_line_ids:
                prescription_repeat = line.repeat
        self.prescription_repeat = prescription_repeat
        # add function to auto generate lines existing medicine
        lines = []
        self.prescription_line_ids = False
        for line in self.prescription_id.prescription_detail_ids:
            data = {}
            data.update({
                'product_id': line.product_id.id,
                # 'repeat': ,
                'scheduled_date': line.scheduled_date,
                'is_done': line.is_done,
                'done_at': line.done_at,
                # link in future done time and 
                'prescription_line_id': line.id,
                # 'state': line.state ,
            })
            lines.append((0, 0, data))
        self.prescription_line_ids = lines

    @api.depends('date', 'date_to')
    def _get_planned_duration(self):
        for rec in self:
            if rec.date and rec.date_to:
                diff = rec.date_to - rec.date
                planned_duration = (diff.days * 24) + (diff.seconds / 3600)
                if rec.planned_duration != planned_duration:
                    rec.planned_duration = planned_duration
                else:
                    rec.planned_duration = rec.manual_planned_duration

    @api.onchange('planned_duration')
    def _inverse_planned_duration(self):
        for rec in self:
            rec.manual_planned_duration = rec.planned_duration
            if rec.date:
                rec.date_to = rec.date + timedelta(hours=rec.planned_duration)

    @api.depends('waiting_date_start', 'waiting_date_end')
    def _compute_waiting_running_duration(self):
        for rec in self:
            if rec.waiting_date_start and rec.waiting_date_end:
                rec.waiting_duration_timer = round(
                    (rec.waiting_date_end - rec.waiting_date_start).total_seconds() / 60.0, 2)
            elif rec.waiting_date_start:
                rec.waiting_duration_timer = round(
                    (fields.Datetime.now() - rec.waiting_date_start).total_seconds() / 60.0, 2)
            else:
                rec.waiting_duration_timer = 0

    @api.depends('date_end', 'date_start')
    def _compute_consulataion_running_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                rec.appointment_duration_timer = round((rec.date_end - rec.date_start).total_seconds() / 60.0, 2)
            elif rec.date_start:
                rec.appointment_duration_timer = round((fields.Datetime.now() - rec.date_start).total_seconds() / 60.0,
                                                       2)
            else:
                rec.appointment_duration_timer = 0

    @api.model
    def default_get(self, fields):
        res = super(Appointment, self).default_get(fields)
        if self._context.get('acs_department_type'):
            department = self.env['hr.department'].search(
                [('department_type', '=', self._context.get('acs_department_type'))], limit=1)
            if department:
                res['department_id'] = department.id
        return res

    def _compute_field_value(self, field):
        if field.name == 'department_type':
            for rec in self:
                if rec.department_id and rec.department_id.id:
                    department = self.env['hr.department'].sudo().search([('id', '=', rec.department_id.id)])
                    rec.write({
                        'department_type': department.department_type
                    })
        else:
            super()._compute_field_value(field)

    def action_create_dental_invoice(self):
        pass

    def update_reminder_dates(self):
        for rec in self:
            if fields.Datetime.now() < rec.date:
                reminder_date = rec.date - timedelta(days=int(rec.company_id.acs_reminder_day)) - timedelta(
                    hours=int(rec.company_id.acs_reminder_hours))
                if reminder_date >= fields.Datetime.now():
                    rec.reminder_date = reminder_date

    def update_appoinemtn_refering(self):
        for rec in self:
            if rec.refered_from_appointment_id and rec.refered_from_appointment_id.refered_to_appointment_id != rec:
                rec.refered_from_appointment_id.refered_to_appointment_id = rec.id

    @api.model
    def send_appointment_reminder(self):
        date_time_now = fields.Datetime.now()
        reminder_appointments = self.sudo().search(
            [('acs_reminder_sent', '=', False), ('state', 'in', ['draft', 'confirm']),
             ('date', '>', fields.Datetime.now()), ('reminder_date', '<=', date_time_now)])
        if reminder_appointments:
            for reminder_appointment in reminder_appointments:
                reminder_appointment.acs_reminder_sent = True
        return reminder_appointments

    @api.onchange('department_id')
    def onchange_department(self):
        res = {}
        if self.department_id:
            physicians = self.env['hms.physician'].search([('department_ids', 'in', self.department_id.id)])
            res['domain'] = {'physician_id': [('id', 'in', physicians.ids)]}
            self.department_type = self.department_id.department_type
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('name', 'New Appointment') == 'New Appointment':
                values['name'] = self.env['ir.sequence'].next_by_code('hms.appointment') or 'New Appointment'
        res = super().create(vals_list)
        for record in res:
            record.update_reminder_dates()
            record.update_appoinemtn_refering()
        return res

    def write(self, values):
        res = super(Appointment, self).write(values)
        # if 'follow_date' in values:
        #     self.sudo()._create_edit_followup_reminder()
        if 'date' in values:
            self.sudo().update_reminder_dates()
        if 'refered_from_appointment_id' in values:
            self.sudo().update_appoinemtn_refering()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        for record in self:
            if record.state not in ('draft', 'cancel'):
                raise UserError(_("You can delete a record in draft or cancelled state only."))

    def print_report(self):
        return self.env.ref('acs_hms.action_appointment_report').report_action(self)

    def action_appointment_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id('acs_hms.acs_appointment_email',
                                                                 raise_if_not_found=False)

        ctx = {
            'default_model': 'hms.appointment',
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

    def acs_appointment_inv_product_data(self, with_product=True):
        product_data = []
        if with_product:
            product_id = self.product_id
            if not product_id:
                raise UserError(_("Please Set Service Charge first."))

            product_data = [{'product_id': product_id}]

        if self.treatment_id.medicine_line_ids:
            for line in self.treatment_id.medicine_line_ids:
                product_data.append({
                    'product_id': line.product_id
                })

        if self.consumable_line_ids:
            product_data.append({
                'name': _("Consumed Product/services"),
            })
            for consumable in self.consumable_line_ids:
                product_data.append({
                    'product_id': consumable.product_id,
                    'quantity': consumable.qty,
                    'lot_id': consumable.lot_id and consumable.lot_id.id or False,
                    'product_uom_id': consumable.product_uom_id.id,
                })

        # ACS: Check if we need it or not as it is getting created in combined
        # invocie call by default. related method is also commented.
        if self._context.get('with_procedure'):
            if self.procedure_to_invoice_ids:
                product_data += self.procedure_to_invoice_ids.get_procedure_invoice_data()

        return product_data

    def acs_appointment_inv_data(self):
        return {
            'ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'physician_id': self.physician_id and self.physician_id.id or False,
            'appointment_id': self.id,
            'hospital_invoice_type': 'appointment',
        }

    # Method to collect other related records data
    def acs_appointment_common_data(self, invoice_id):
        """
            Currently we are managing  follwoing related records invoicing:
            1> Procedures: that are already coverd in acs_appointment_inv_product_data and dene here also
            2> Pharmacy: done in pharmacy module
            3> Surgery: done in surgey module
            4> Laboratory: done in hms Laboratory module
            5> Radiology: done in hms Radiology module
        """
        # Procedure Invoicing
        data = self.procedure_to_invoice_ids.acs_common_invoice_procedure_data(invoice_id)
        return data

    # mehtod to create invoice on related records like done in hospitalization
    def acs_appointment_common_invoicing(self, invoice_id):
        data = self.acs_appointment_common_data(invoice_id)
        # create Invoice lines only if invoice is passed
        if invoice_id:
            for line in data:
                inv_line = self.with_context(acs_pricelist_id=self.pricelist_id.id).acs_create_invoice_line(line,
                                                                                                            invoice_id)
        return data

    def create_invoice(self):
        inv_data = self.acs_appointment_inv_data()
        product_data = self.acs_appointment_inv_product_data()
        acs_context = {'commission_partner_id': self.physician_id.partner_id.id}
        if self.pricelist_id:
            acs_context.update({'acs_pricelist_id': self.pricelist_id.id})
        invoice = self.with_context(acs_context).acs_create_invoice(partner=self.patient_id.partner_id,
                                                                    patient=self.patient_id, product_data=product_data,
                                                                    inv_data=inv_data)
        self.invoice_id = invoice.id
        self.acs_appointment_common_invoicing(invoice)
        if self.state == 'to_invoice':
            self.appointment_done()

        if self.state == 'draft' and not self._context.get('avoid_confirmation'):
            if self.invoice_id and not self.company_id.acs_check_appo_payment:
                self.appointment_confirm()

    def create_consumed_prod_invoice(self):
        inv_data = self.acs_appointment_inv_data()
        inv_data['create_stock_move'] = True
        product_data = []
        for treat in self.treatment_ids:
            # if not treat.consumable_line_ids:
            #     raise UserError(_("There is no consumed product to invoice."))

            # product_data = self.acs_appointment_inv_product_data()
            if treat.medicine_line_ids:
                for line in treat.medicine_line_ids:
                    product_data.append({
                        'product_id': line.product_id,
                        'lot_id': line.acs_lot_id and line.acs_lot_id.id or False,
                    })

            if treat.consumable_line_ids:
                product_data.append({
                    'name': _("Consumed Product/services"),
                })
                for consumable in treat.consumable_line_ids:
                    product_data.append({
                        'product_id': consumable.product_id,
                        'quantity': consumable.qty,
                        'lot_id': consumable.lot_id and consumable.lot_id.id or False,
                        'product_uom_id': consumable.product_uom_id.id,
                    })

        pricelist_context = {}
        if self.pricelist_id:
            pricelist_context = {'acs_pricelist_id': self.pricelist_id.id}
        invoice = self.with_context(pricelist_context).acs_create_invoice(partner=self.patient_id.partner_id,
                                                                          patient=self.patient_id,
                                                                          product_data=product_data, inv_data=inv_data)
        self.consumable_invoice_id = invoice.id
        self.acs_appointment_common_invoicing(invoice)
        # if self.state == 'to_after_care':
        #     self.appointment_done()

    def action_create_invoice_with_procedure(self):
        return self.with_context(with_procedure=True).create_invoice()

    def view_invoice(self):
        appointment_invoices = self.invoice_ids
        action = self.acs_action_view_invoice(appointment_invoices)
        action['context'].update({
            'default_partner_id': self.patient_id.partner_id.id,
            'default_patient_id': self.patient_id.id,
            'default_appointment_id': self.id,
            'default_ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'default_physician_id': self.physician_id and self.physician_id.id or False,
            'default_hospital_invoice_type': 'appointment',
            'default_ref': self.name,
        })
        return action

    def action_refer_doctor(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_physician_id': self.physician_id.id,
            'default_refered_from_appointment_id': self.id
        }
        action['views'] = [(self.env.ref('acs_hms.view_hms_appointment_form').id, 'form')]
        return action

    def action_create_evaluation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_evaluation_popup")
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id,
                             'default_appointment_id': self.id}
        return action

    @api.onchange('patient_id', 'date')
    def onchange_patient_id(self):
        if self.patient_id:
            self.age = self.patient_id.age
            self.mobile = self.patient_id.mobile
            self.email = self.patient_id.email
            followup_days = self.env.user.company_id.followup_days
            followup_day_limit = (datetime.now() - timedelta(days=followup_days)).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)
            appointment_id = self.search([('patient_id', '=', self.patient_id.id), ('date', '>=', followup_day_limit),
                                          ('state', 'not in', ['cancel', 'draft'])])

            # Avoid setting physician if already there from treatment or manually selected.
            if not self.physician_id:
                self.physician_id = self.patient_id.primary_physician_id and self.patient_id.primary_physician_id.id
            if appointment_id and followup_days:
                self.consultation_type = 'followup'
                if self.env.user.company_id.followup_product_id:
                    self.product_id = self.env.user.company_id.followup_product_id.id
            else:
                self.consultation_type = 'consultation'

    # @api.onchange('physician_id', 'department_id', 'consultation_type')
    # def onchange_physician(self):
    #     product_id = False
    #     # ACS: First check configuration on department.
    #     if self.acs_department_id:
    #         # ACS: To avoid portal access error research department here.
    #         if self.consultation_type == 'followup':
    #             if self.acs_department_id.followup_service_id:
    #                 product_id = self.acs_department_id.followup_service_id.id

    #         elif self.acs_department_id.consultaion_service_id:
    #             product_id = self.acs_department_id.consultaion_service_id.id

    #     if self.physician_id:
    #         if self.consultation_type == 'followup':
    #             if self.physician_id.followup_service_id:
    #                 product_id = self.physician_id.followup_service_id.id

    #         elif self.physician_id.consultaion_service_id:
    #             product_id = self.physician_id.consultaion_service_id.id

    #         if self.physician_id.appointment_duration and not self._context.get('acs_online_transaction'):
    #             self.planned_duration = self.physician_id.appointment_duration

    #     if product_id:
    #         self.product_id = product_id

    def appointment_confirm(self):
        if (not self._context.get('acs_online_transaction')) and (not self.invoice_exempt):
            if self.appointment_invoice_policy == 'advance' and not self.invoice_id:
                raise UserError(_('Invoice is not created yet'))

            elif self.invoice_id and self.company_id.acs_check_appo_payment and self.payment_state not in ['in_payment',
                                                                                                           'paid']:
                raise UserError(_('Invoice is not Paid yet.'))

        if not self.user_id:
            self.user_id = self.env.user.id

        if not self.consent_ids:
            action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_schedule_consent_wiz")
            return action

        if self.patient_id.email and (
                self.company_id.acs_auto_appo_confirmation_mail or self._context.get('acs_online_transaction')):
            try:
                template = self.env.ref('acs_hms.acs_appointment_email')
                treatment = ', '.join([t.name for t in self.procedure_ids])
                email_values = {'treatment': treatment}
                template_appointment_creation = template.with_context(**email_values).sudo().send_mail(self.id,
                                                                                                       raise_exception=False,
                                                                                                       force_send=True)
                if template_appointment_creation:
                    template.reset_template()
                    # Get the mail template for the sale order confirmation.
                    template_consent = self.env.ref('acs_hms.appointment_consent_form_email')
                    for itms_consent_id in self.consent_ids:
                        # Generate the PDF attachment.
                        pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                            'itms_consent_form.report_consent', res_ids=[itms_consent_id.id])
                        attachment = self.env['ir.attachment'].create({
                            'name': itms_consent_id.name,
                            'type': 'binary',
                            'raw': pdf_content,
                            'res_model': itms_consent_id._name,
                            'res_id': itms_consent_id.id
                        })
                        # Add the attachment to the mail template.
                        template_consent.attachment_ids += attachment
                    # Send the email.
                    template_consent_creation = template_consent.sudo().send_mail(
                        self.id, raise_exception=False, force_send=True)
                    if template_consent_creation:
                        template_consent.reset_template()
                        self.waiting_date_start = datetime.now()
                        self.waiting_duration = 0.1
                        self.state = 'confirm'
            except Exception as e:
                _logger.warning('Failed to send appointment confirmation email: %s', e)

    # def consent_forms_confirm(self):
    #     if (not self._context.get('acs_online_transaction')) and (not self.invoice_exempt):
    #         if self.appointment_invoice_policy == 'advance' and not self.invoice_id:
    #             raise UserError(_('Invoice is not created yet'))
    #
    #         elif self.invoice_id and self.company_id.acs_check_appo_payment and self.payment_state not in ['in_payment',
    #                                                                                                        'paid']:
    #             raise UserError(_('Invoice is not Paid yet.'))
    #
    #     if not self.user_id:
    #         self.user_id = self.env.user.id
    #
    #     if self.patient_id.email and (
    #             self.company_id.acs_auto_appo_confirmation_mail or self._context.get('acs_online_transaction')):
    #         try:
    #             template_consent = self.env.ref('acs_hms.appointment_consent_form_email')
    #             for itms_consent_id in self.consent_ids:
    #                 # Generate the PDF attachment.
    #                 pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
    #                     'itms_consent_form.report_consent', res_ids=[itms_consent_id.id])
    #                 attachment = self.env['ir.attachment'].create({
    #                     'name': itms_consent_id.name,
    #                     'type': 'binary',
    #                     'raw': pdf_content,
    #                     'res_model': itms_consent_id._name,
    #                     'res_id': itms_consent_id.id
    #                 })
    #                 # Add the attachment to the mail template.
    #                 template_consent.attachment_ids += attachment
    #             # Send the email.
    #             template_consent_creation = template_consent.sudo().send_mail(
    #                 self.id, raise_exception=False, force_send=True)
    #             if template_consent_creation:
    #                 template_consent.reset_template()
    #
    #         except Exception as e:
    #             _logger.warning('Failed to send appointment confirmation email: %s', e)
    #
    #     self.waiting_date_start = datetime.now()
    #     self.waiting_duration = 0.1
    #     self.state = 'confirm'
    def appointment_waiting(self):
        self.state = 'waiting'
        self.waiting_date_start = datetime.now()
        self.waiting_duration = 0.1

    def appointment_waiting_manual(self):
        try:
            self.state = self.state = 'confirm_consent'
        except Exception as e:
            _logger.warning('Failed to update appointment confirmation email: %s', e)

    def appointment_consultation(self):
        self.waiting_date_start = datetime.now()
        if not self.waiting_date_start:
            raise UserError(('No waiting start time defined.'))
        datetime_diff = datetime.now() - self.waiting_date_start
        m, s = divmod(datetime_diff.total_seconds(), 60)
        h, m = divmod(m, 60)
        self.waiting_duration = float(('%0*d') % (2, h) + '.' + ('%0*d') % (2, m * 1.677966102))
        self.state = 'in_consultation'
        self.waiting_date_end = datetime.now()
        self.date_start = datetime.now()

    def action_pause(self):
        self.state = 'pause'
        self.pause_date_start = datetime.now()

        if self.date_start:
            datetime_diff = datetime.now() - self.date_start
            m, s = divmod(datetime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            self.appointment_duration = float(
                ('%0*d') % (2, h) + '.' + ('%0*d') % (2, m * 1.677966102)) - self.pause_duration
        self.date_end = datetime.now()

    def action_start_paused(self):
        self.state = 'in_consultation'
        self.pause_date_end = datetime.now()
        self.date_end = False
        datetime_diff = datetime.now() - self.pause_date_start
        m, s = divmod(datetime_diff.total_seconds(), 60)
        h, m = divmod(m, 60)
        self.pause_duration += float(('%0*d') % (2, h) + '.' + ('%0*d') % (2, m * 1.677966102))

    def consultation_done(self):
        if self.date_start:
            datetime_diff = datetime.now() - self.date_start
            m, s = divmod(datetime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            self.appointment_duration = float(
                ('%0*d') % (2, h) + '.' + ('%0*d') % (2, m * 1.677966102)) - self.pause_duration
        self.date_end = datetime.now()
        if (self.invoice_exempt or self.invoice_id) and not (
                self.consumable_line_ids and self.appointment_invoice_policy == 'advance' and not self.invoice_exempt and not self.consumable_invoice_id):
            self.appointment_done()
        # else:
        #     self.state = 'to_after_care'
        if self.consumable_line_ids:
            self.consume_appointment_material()
        # if self.prescription_id:
        #     for line in self.prescription_id.prescription_line_ids:
        #         line.repeat -= 1
        if self.treatment_ids and self.treatment_ids.prescription_ids:
            lines = self.treatment_ids.prescription_ids.prescription_line_ids
            for line in lines:
                line.repeat -= 1
        return {
            'name': _('Add Treatment'),
            'type': 'ir.actions.act_window',
            'res_model': 'hms.treatment',
            'view_mode': 'form',
            'view_id': self.env.ref('acs_hms.view_hospital_hms_treatment_form').id,
            'target': 'current',
        }
        # self.appointment_done()

    def appointment_done(self):
        self.state = 'done'
        template_aftercare = self.env.ref('acs_hms.appointment_aftercare_email')
        if len(self.aftercare_ids) <= 0:
            raise UserError(_('Please select Aftercare form to complete the appointment'))

        attachments = []
        for aftercare in self.aftercare_ids:
            if aftercare:
                pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                    'itms_consent_form.action_report_aftercare', res_ids=[aftercare.id])
                aftercare_attachment_id = self.env['ir.attachment'].create({
                    'name': aftercare.name,
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': aftercare._name,
                    'res_id': aftercare.id
                })
                attachments.append(aftercare_attachment_id.id)
        template_aftercare.attachment_ids = attachments
        medicine_line_ids = []
        treatment_notes = []
        if self.treatment_ids:
            for treat in self.treatment_ids:
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
                                    {'product_name': product_name, 'medicine_area': medicine_area, 'amount': amount,
                                     'batch_number': batch_number, 'medicine_technique': medicine_technique,
                                     'medicine_depth': medicine_depth, 'medicine_method': medicine_method,
                                     'template': treat.template_id.name})
                    if treat.template_id:
                        finding = treat.finding or ''
                        template = treat.template_id.name
                        treatment_notes.append({'template': template, 'finding': finding})
        email_values = {'medicine_line_ids': medicine_line_ids, 'treatment_notes': treatment_notes}
        is_sent = template_aftercare.with_context(**email_values).sudo().send_mail(self.id, raise_exception=False,
                                                                                   force_send=True)
        if is_sent:
            template_aftercare.reset_template()
        if self.company_id.sudo().auto_followup_days:
            self.follow_date = self.date + timedelta(days=self.company_id.sudo().auto_followup_days)

    def appointment_cancel(self):
        self.state = 'cancel'
        self.waiting_date_start = False
        self.waiting_date_end = False
        if self.sudo().invoice_id and self.sudo().invoice_id.state == 'draft':
            self.sudo().invoice_id.unlink()

    def appointment_draft(self):
        self.state = 'draft'

    def action_prescription(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        prescription_ids = self.env['prescription.order'].search(
            [
                # ('state', '=', 'prescription'),
                ('patient_id', '=', self.patient_id.id),
                # ('expire_date', '>=', fields.Date.today())
            ])
        action['domain'] = [('id', 'in', prescription_ids.ids)]
        # action['domain'] = [('appointment_id', '=', self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_physician_id': self.physician_id.id,
            'default_diseases_ids': [(6, 0, self.diseases_ids.ids)],
            'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
            'default_appointment_id': self.id}
        action['views'] = [(self.env.ref('acs_hms.view_hms_prescription_order_select_tree').id, 'tree'),
                           (self.env.ref('acs_hms.view_hms_prescription_order_form').id, 'form')]
        return action

    def multiple_consent_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("document_page.action_page")
        action['domain'] = []
        action['views'] = [(self.env.ref('document_page.view_wiki_tree').id, 'tree'),
                           (self.env.ref('document_page.view_wiki_form').id, 'form')]
        action['target'] = 'new'
        return action

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        ctx = self._context
        if self._context.get('autofocus', '') == 'autofocus' and view_type == 'form':
            for node in arch.xpath("//page[@name='prescription_line_ids']"):
                node.set('autofocus', 'autofocus')
        return arch, view

    def button_pres_req(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        action['domain'] = [('appointment_id', '=', self.id)]
        action['views'] = [(self.env.ref('acs_hms.view_hms_prescription_order_form').id, 'form')]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_physician_id': self.physician_id.id,
            'default_diseases_ids': [(6, 0, self.diseases_ids.ids)],
            'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
            'default_appointment_id': self.id}
        return action

    treatment_count = fields.Integer(compute='_rec_count', string='# Treatments')

    def _rec_count(self):
        for rec in self:
            rec.treatment_count = len(self.patient_id.treatment_ids.filtered(lambda trt: trt.state in ['running']))
            rec.prescription_count = len(self.env['prescription.order'].search(
                [
                    # ('state', '=', 'prescription'),
                    ('patient_id', '=', self.patient_id.id),
                    # ('expire_date', '>=', fields.Date.today())
                ]))

    def action_view_treatment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.acs_action_form_hospital_treatment")
        action['context'] = {
            'default_appointment_ids': [(6, 0, self.ids)],
            'default_patient_id': self.patient_id.id,
            'acs_current_appointment': self.id
        }
        running_treatment_ids = self.patient_id.treatment_ids.filtered(lambda trt: trt.state in ['running'])
        action['domain'] = [('id', 'in', running_treatment_ids.ids)]
        # action['views'] = [(self.env.ref('acs_hms.view_acs_hms_treatment_appointment_tree').id, 'tree')]

        # action['views'] = [(self.env.ref('acs_hms.view_hospital_hms_treatment_form').id, 'form')]
        #
        # if self.treatment_id:
        #     action['domain'] = [('id', '=', self.treatment_id.id)]
        #     action['res_id'] = self.treatment_id.id
        # elif self.patient_id.treatment_ids.filtered(lambda trt: trt.state in ['draft', 'running']):
        #     running_treatment_ids = self.patient_id.treatment_ids.filtered(lambda trt: trt.state in ['draft', 'running'])
        #     action['domain'] = [('id', 'in', running_treatment_ids.ids)]
        #     action['views'] = [(self.env.ref('acs_hms.view_acs_hms_treatment_appointment_tree').id, 'tree')]
        return action

    def acs_get_consume_locations(self):
        if not self.company_id.appointment_usage_location_id:
            raise UserError(_('Please define a appointment location where the consumables will be used.'))
        if not self.company_id.appointment_stock_location_id:
            raise UserError(_('Please define a appointment location from where the consumables will be taken.'))

        dest_location_id = self.company_id.appointment_usage_location_id.id
        source_location_id = self.company_id.appointment_stock_location_id.id
        return source_location_id, dest_location_id

    def consume_appointment_material(self):
        for rec in self:
            source_location_id, dest_location_id = rec.acs_get_consume_locations()
            for line in rec.consumable_line_ids.filtered(lambda s: not s.move_id):
                if line.product_id.is_kit_product:
                    move_ids = []
                    for kit_line in line.product_id.acs_kit_line_ids:
                        if kit_line.product_id.tracking != 'none':
                            raise UserError(
                                "In Consumable lines Kit product with component having lot/serial tracking is not allowed. Please remove such kit product from consumable lines.")
                        move = self.consume_material(source_location_id, dest_location_id,
                                                     {'product': kit_line.product_id,
                                                      'qty': kit_line.product_qty * line.qty})
                        move.appointment_id = rec.id
                        move_ids.append(move.id)
                    # Set move_id on line also to avoid
                    line.move_id = move.id
                    line.move_ids = [(6, 0, move_ids)]
                else:
                    move = self.consume_material(source_location_id, dest_location_id,
                                                 {'product': line.product_id, 'qty': line.qty,
                                                  'lot_id': line.lot_id and line.lot_id.id or False, })
                    move.appointment_id = rec.id
                    line.move_id = move.id

    def action_view_patient_procedures(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_procedure")
        domain = [('appointment_ids', 'in', self.id)]
        if self.treatment_id:
            domain = ['|', ('treatment_id', '=', self.treatment_id.id)] + domain
        action['domain'] = domain
        action['context'] = {
            'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
            'default_appointment_ids': [(6, 0, [self.id])],
            'default_patient_id': self.patient_id.id,
            'default_physician_id': self.physician_id.id,
            'default_department_id': self.department_id.id
        }
        return action

    def get_acs_kit_lines(self):
        if not self.acs_kit_id:
            raise UserError("Please Select Kit first.")

        lines = []
        for line in self.acs_kit_id.acs_kit_line_ids:
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_id': line.product_id.uom_id.id,
                'qty': line.product_qty * self.acs_kit_qty,
            }))
        self.consumable_line_ids = lines

    # Create/Edit Followup activity if needed
    def _create_edit_followup_reminder(self):
        Activity = self.env['mail.activity']
        default_activity_type = self.env['mail.activity.type'].search([], limit=1)
        res_model = self.env['ir.model'].sudo().search([('model', '=', self._name)])
        for rec in self:
            if rec.follow_date:
                company = rec.company_id.sudo() or self.env.company.sudo()
                activity_type = company.acs_followup_activity_type_id or default_activity_type
                if not activity_type:
                    raise UserError(_("Please Set Followup activity Type on Configiration."))

                followup_date = rec.follow_date - timedelta(days=1)
                if not rec.user_id:
                    rec.user_id = self.env.user.id
                user_id = rec.user_id

                existing_activity = Activity.search([('res_id', '=', rec.id), ('res_model_id', '=', self._name),
                                                     ('activity_type_id', '=', activity_type.id),
                                                     ('user_id', '=', user_id.id)])
                if existing_activity:
                    existing_activity.date_deadline = followup_date
                else:
                    activity_vals = {
                        'res_id': rec.id,
                        'res_model_id': res_model.id,
                        'activity_type_id': activity_type.id,
                        'summary': _('Appointment Follow up'),
                        'date_deadline': followup_date,
                        'automated': True,
                        'user_id': user_id.id
                    }
                    self.env['mail.activity'].with_context(mail_activity_quick_update=True).create(activity_vals)

    def cancel_old_appointments(self):
        parameter = self.env['ir.config_parameter']
        yesterday = fields.Datetime.now().replace(hour=0, minute=0, second=0)
        if parameter.sudo().get_param('acs_hms.cancel_old_appointment'):
            previous_appointments = self.env['hms.appointment'].search(
                [('date', '<=', yesterday), ('state', 'in', ['draft', 'confirm'])])
            for appointment in previous_appointments:
                appointment.with_context(cancel_from_cron=True).appointment_cancel()
        return

    def acs_reschedule_appointments(self, reschedule_time):
        for rec in self:
            rec.date = rec.date + timedelta(hours=reschedule_time)
            rec.date_to = rec.date_to + timedelta(hours=reschedule_time)

    @api.model
    def send_sms_appointments_reminder(self):
        from twilio.rest import Client
        date_time_now = fields.Datetime.now()
        gateway = self.env['sms.gateway.config'].search([('sms_gateway_id.name', '=', 'twilio')], limit=1)
        if gateway:
            reminder_appointments = self.sudo().search(
                [('state', 'in', ['draft', 'confirm', 'confirm_consent', 'in_consultation', 'to_after_care']),
                 ('schedule_date', '<=', fields.Datetime.now().date())])
            client = Client(gateway.twilio_account_sid,
                            gateway.twilio_auth_token)
            for reminder in reminder_appointments:
                try:
                    message = """
                    Dear {nurse},
                    This is a friendly reminder that you have a appointment scheduled in a few days, details:
                    Reference Number: {appointment}
                    Schedule Date: {date}
                    """.format(nurse=reminder.nurse_id.name, appointment=reminder.name, date=reminder.schedule_date)
                    sms_to = reminder.nurse_id.phone
                    for number in sms_to.split(','):
                        if number:
                            client.messages.create(
                                body=message,
                                from_=gateway.twilio_phone_number,
                                to=number
                            )
                    history = self.env['sms.history'].sudo().create({
                        'sms_gateway_id': gateway.sms_gateway_id.id,
                        'sms_mobile': sms_to,
                        'sms_text': message
                    })
                except Exception as e:
                    pass
        return True

    @api.onchange('consultation_type')
    def _done_add_prescription(self):
        for rec in self:
            if rec.consultation_type == 'followup':
                Prescription = rec.env['prescription.order']
                prescription_ids = Prescription.search([('patient_id', '=', rec.patient_id.id)])
                # if prescription_ids:
                #     rec.prescription_id = prescription_ids[-1]


class StockMove(models.Model):
    _inherit = "stock.move"

    appointment_id = fields.Many2one('hms.appointment', string="Appointment", ondelete="restrict")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class PrescriptionLine(models.Model):
    _name = 'appointment.prescription.line'
    _rec_name = "product_id"
    _order = "scheduled_date"

    appointment_id = fields.Many2one('hms.appointment', string='Order')
    done_in_appointment_id = fields.Many2one('hms.appointment', string='Done in Order')
    is_invoiced = fields.Boolean()

    name = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Medicine')
    qty = fields.Integer(string='Quantity')
    repeat = fields.Integer(string='Repeat')
    scheduled_date = fields.Date(string='Scheduled Date')
    done_at = fields.Datetime(string='Done At')
    is_done = fields.Boolean(string='Done')
    state = fields.Selection(
        [('done', 'Done'),
         ('processing', 'Processing'),
         ('waiting', 'Waiting')], string='State', default='waiting')
    treatment_id = fields.Many2one("hms.treatment", string='Treatment', compute='get_treatment')
    prescription_line_id = fields.Many2one("prescription.detail", string="Prescription Detail")

    @api.depends('is_done')
    def _done_process(self):
        for rec in self:
            rec.done_at = fields.Datetime.now()

    def openWizard(self):
        print("self.product_id.id,", self.product_id.id, self.id)
        if self.treatment_id:
            return {'name': f"Treatment Notes",
                    'view_mode': 'form',
                    'res_model': 'hms.treatment',
                    'view_id': self.env.ref('acs_hms.view_hospital_hms_treatment_form').id,
                    'res_id': self.treatment_id.id,
                    # 'target': 'new',
                    'type': 'ir.actions.act_window',
                    'context': {},
                    }
        else:
            return {
                'name': f"Treatment Notes",
                'view_mode': 'form',
                'res_model': 'hms.treatment',
                'view_id': self.env.ref('acs_hms.view_hospital_hms_treatment_form').id,
                'res_id': False,
                'type': 'ir.actions.act_window',
                # 'target': 'new',
                'context': {'default_patient_id': self.appointment_id.patient_id.id,
                            'default_appointment_id': self.appointment_id.id,
                            'default_appointment_prescription_line_id': self.id,
                            'default_medicine_line_ids': [(0, 0, {
                                'product_id': self.product_id.id,
                                # 'field2': 'value2',
                            })],
                            }
            }

    def get_treatment(self):
        for rec in self:
            treatment = self.env['hms.treatment'].search([('appointment_prescription_line_id', '=', rec.id)], limit=1)
            if len(treatment) > 0:
                rec.treatment_id = treatment[0].id
            else:
                rec.treatment_id = False

# -*- coding: utf-8 -*-
import base64
import json
import magic
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta


class ACSTreatment(models.Model):
    _name = 'hms.treatment'
    _description = "Treatment"
    _order = "date DESC"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'acs.documnt.mixin']

    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)

    @api.model
    def _get_service_id(self):
        registration_product = False
        if self.env.user.company_id.treatment_registration_product_id:
            registration_product = self.env.user.company_id.treatment_registration_product_id.id
        return registration_product

    @api.model
    def _default_photos(self):
        vals = []
        templates = self.env['treatment.photos.template'].search([])
        for tmp in templates:
            vals.append((0, 0, {
                'name': tmp.name
            }))
        return vals

    def _rec_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)
            rec.patient_procedure_count = len(rec.patient_procedure_ids)

    READONLY_STATES = {'cancel': [('readonly', False)], 'done': [('readonly', False)]}

    name = fields.Char(string='Name', readonly=True, index=True, copy=False, tracking=True)
    display_name = fields.Char(compute='_compute_display_name', string='Treatment Note Title')
    subject = fields.Char(string='Subject', tracking=True, states=READONLY_STATES)
    patient_id = fields.Many2one('hms.patient', 'Patient', required=True, index=True, states=READONLY_STATES,
                                 tracking=True)
    department_id = fields.Many2one('hr.department', ondelete='restrict', string='Department',
                                    domain=[('patient_department', '=', True)], states=READONLY_STATES, tracking=True)
    image_128 = fields.Binary(related='patient_id.image_128', string='Image', readonly=True)
    date = fields.Datetime(string='Date of Treatment', default=fields.Datetime.now, states=READONLY_STATES)
    healed_date = fields.Date(string='Healed Date', states=READONLY_STATES)
    end_date = fields.Date(string='End Date', help='End of treatment date', states=READONLY_STATES)
    diagnosis_id = fields.Many2one('hms.diseases', string='Medicine', states=READONLY_STATES)
    nurse_id = fields.Many2one('res.users', 'Clinician', domain=[('physician_id', '=', False)],
                               default=lambda self: self.env.user.id, required=True)
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Prescriber', states=READONLY_STATES,
                                   tracking=True)
    attending_physician_ids = fields.Many2many('hms.physician', 'hosp_treat_doc_rel', 'treat_id', 'doc_id',
                                               string='Primary Doctors',
                                               states=READONLY_STATES)
    prescription_line_ids = fields.One2many('prescription.line', 'treatment_id', 'Prescription',
                                            states=READONLY_STATES)
    medicine_line_ids = fields.One2many('treatment.medicine.line', 'treatment_id', 'Medicine',
                                        states=READONLY_STATES)
    template_id = fields.Many2one('treatment.template', 'Template Note')
    template_ids = fields.Many2many('treatment.template', 'treatment_template_rel', 'treatment_id', 'template_id')
    finding = fields.Html(string="Findings")
    finding_tmp = fields.Html(string="Findings Tmp")
    appointment_ids = fields.One2many('hms.appointment', 'treatment_id', string='Appointments',
                                      states=READONLY_STATES)
    appointment_count = fields.Integer(compute='_rec_count', string='# Appointments')
    appointment_id = fields.Many2one("hms.appointment", string="Appointment")
    appointment_prescription_line_id = fields.Many2one('appointment.prescription.line', string="Appointment line")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, copy=False, states=READONLY_STATES, tracking=True)
    description = fields.Char(string='Treatment Description', states=READONLY_STATES)

    is_allergy = fields.Boolean(string='Allergic Disease', states=READONLY_STATES)
    pregnancy_warning = fields.Boolean(string='Pregnancy warning', states=READONLY_STATES)
    lactation = fields.Boolean('Lactation', states=READONLY_STATES)
    disease_severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ], string='Severity', index=True, states=READONLY_STATES)
    disease_status = fields.Selection([
        ('acute', 'Acute'),
        ('chronic', 'Chronic'),
        ('unchanged', 'Unchanged'),
        ('healed', 'Healed'),
        ('improving', 'Improving'),
        ('worsening', 'Worsening'),
    ], string='Status of the disease', index=True, states=READONLY_STATES)
    is_infectious = fields.Boolean(string='Infectious Disease', states=READONLY_STATES)
    allergy_type = fields.Selection([
        ('da', 'Drug Allergy'),
        ('fa', 'Food Allergy'),
        ('ma', 'Misc Allergy'),
        ('mc', 'Misc Contraindication'),
    ], string='Allergy type', index=True, states=READONLY_STATES)
    age = fields.Char(string='Age when diagnosed', states=READONLY_STATES)
    patient_disease_id = fields.Many2one('hms.patient.disease', string='Patient Disease', states=READONLY_STATES)
    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='restrict', copy=False)
    company_id = fields.Many2one('res.company', ondelete='restrict', states=READONLY_STATES,
                                 string='Clinic', default=lambda self: self.env.company)
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'treatment_medical_alert_rel', 'treatment_id', 'alert_id',
                                         string='Medical Alerts', related="patient_id.medical_alert_ids")
    alert_count = fields.Integer(compute='_get_alert_count', default=0)
    registration_product_id = fields.Many2one('product.product', default=_get_service_id, string="Registration Service")
    department_type = fields.Selection(related='department_id.department_type', string="Treatment Department",
                                       store=True)

    patient_procedure_ids = fields.One2many('acs.patient.procedure', 'treatment_id', 'Patient Procedures')
    patient_procedure_count = fields.Integer(compute='_rec_count', string='# Patient Procedures')
    procedure_group_id = fields.Many2one('procedure.group', ondelete="set null", string='Procedure Group',
                                         states=READONLY_STATES)

    consumable_line_ids = fields.One2many('hms.consumable.line', 'treatment_id',
                                          string='Consumable Line', states=READONLY_STATES, copy=False)
    order_id = fields.Many2one('sale.order', string='Sale Order', copy=False, readonly=1)

    # photos
    # attachment_front_ids = fields.Many2many('ir.attachment', 'treatment_attachment_front_rel', 'attachment_id',
    #                                         'treatment_id', string='Front View')
    # attachment_right_ids = fields.Many2many('ir.attachment', 'treatment_attachment_right_rel', 'attachment_id',
    #                                         'treatment_id', string='Right Profile')
    # attachment_left_ids = fields.Many2many('ir.attachment', 'treatment_attachment_left_rel', 'attachment_id',
    #                                        'treatment_id', string='Left Profile')
    # attachment_oblique_right_ids = fields.Many2many('ir.attachment', 'treatment_attachment_oblique_right_rel', 'attachment_id',
    #                                                 'treatment_id', string='Oblique Right')
    # attachment_oblique_left_ids = fields.Many2many('ir.attachment', 'treatment_attachment_oblique_left_rel', 'attachment_id',
    #                                                'treatment_id', string='Oblique Left')
    # attachment_top_ids = fields.Many2many('ir.attachment', 'treatment_attachment_top_rel', 'attachment_id',
    #                                       'treatment_id', string='Top View')
    # attachment_bottom_ids = fields.Many2many('ir.attachment', 'treatment_attachment_bottom_rel', 'attachment_id',
    #                                          'treatment_id', string='Bottom View')
    # attachment_back_ids = fields.Many2many('ir.attachment', 'treatment_attachment_back_rel', 'attachment_id',
    #                                        'treatment_id', string='Back View')

    prescription_ids = fields.Many2many('prescription.order', 'prescription_treatment_rel', 'prescription_id',
                                        'treatment_id',
                                        string='Prescriptions')
    available_prescription_ids = fields.Many2many('prescription.order', 'prescription_treatment_available_rel',
                                                  'prescription_id', 'treatment_id',
                                                  string='Prescriptions', compute='_compute_available_prescription_ids')
    photos_ids = fields.One2many('treatment.photos', 'treatment_id',
                                 string='Photos', states=READONLY_STATES, default=lambda self: self._default_photos(),
                                 copy=False)
    # add 8 images: front view, right profile, left profile, oblique right, oblique left, top view, bottom view, back view,
    front_view = fields.Binary(string='Front View', attachment=True)
    right_profile = fields.Binary(string='Right Profile', attachment=True)
    left_profile = fields.Binary(string='Left Profile', attachment=True)
    oblique_right = fields.Binary(string='Oblique Right', attachment=True)
    oblique_left = fields.Binary(string='Oblique Left', attachment=True)
    top_view = fields.Binary(string='Top View', attachment=True)
    bottom_view = fields.Binary(string='Bottom View', attachment=True)
    back_view = fields.Binary(string='Back View', attachment=True)
    # preview_img_view = fields.Binary(string='Preview Image')
    employee_id = fields.Many2one('hr.employee', compute='_compute_employee_id', string='Employee')

    request_prescription_ids = fields.One2many('prescription.order', 'treatment_id', 'Request Prescription', copy=False)

    # Photo form
    # attachment_ids = fields.Many2many(comodel_name='ir.attachment')
    attachment_ids = fields.One2many(
        'patient.document', 'res_id',
        string='Attachments', domain=[('display_type', '=', 'after')],
        readonly=False
    )
    attachment_copy_ids = fields.Many2many(
        'patient.document', 'res_id',
        string='Attachments',
        readonly=False
    )
    photo = fields.Binary(string='Photo')

    attachment_before_ids = fields.One2many(
        'patient.document', 'res_id',
        string='Attachments', domain=[('display_type', '=', 'before')],
        readonly=False
    )
    attachment_before_copy_ids = fields.Many2many(
        'patient.document', 'res_id',
        string='Attachments',
        readonly=False
    )
    photo_before = fields.Binary(string='Photo Before')
    is_invisible = fields.Boolean(compute="_compute_is_invisible")
    is_invisible_before = fields.Boolean(compute="_compute_is_invisible_before")

    aftercare_ids = fields.One2many(
        'patient.aftercare',
        'treatment_id',
        'Aftercare',
        compute="_compute_aftercare_ids",
        store=True,
        readonly=False)

    @api.depends(
        'medicine_line_ids',
        'medicine_line_ids.product_id',
        'medicine_line_ids.product_id.aftercare_id')
    def _compute_aftercare_ids(self):
        for rec in self:
            rec.aftercare_ids = False
            product_ids = ''
            product_ids = rec.mapped('medicine_line_ids.product_id')
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
                    'treatment_id': rec.id,
                }
                rec.aftercare_ids = [(0, 0, aftercare_val)]

    def action_print(self):
        return self.env.ref('acs_hms.action_treatment_report').report_action(self)

    @api.depends('template_ids')
    def _compute_display_name(self):
        for record in self:
            record.display_name = False
            treatment = ', '.join([t.name for t in record.template_ids])
            if treatment:
                record.display_name = treatment

    @api.depends('attachment_ids')
    def _compute_is_invisible(self):
        for rec in self:
            is_invisible = True
            if rec.attachment_ids:
                is_invisible = False
            rec.is_invisible = is_invisible

    @api.depends('attachment_before_ids')
    def _compute_is_invisible_before(self):
        for rec in self:
            is_invisible_before = True
            if rec.attachment_before_ids:
                is_invisible_before = False
            rec.is_invisible_before = is_invisible_before

    @api.onchange('photo')
    def onchange_photo(self):
        if self.photo:
            self.upload_file()
            self.is_invisible = False
            self.photo = False

    @api.onchange('photo_before')
    def onchange_photo_before(self):
        if self.photo_before:
            self.upload_file_before()
            self.is_invisible_before = False
            self.photo_before = False

    @api.onchange('attachment_ids')
    def onchange_attachment_ids(self):
        if not self.attachment_ids:
            self.is_invisible = True

    @api.onchange('attachment_before_ids')
    def onchange_attachment_before_ids(self):
        if not self.attachment_before_ids:
            self.is_invisible_before = True

    def upload_file(self, photo=False):
        if not photo:
            photo = self.photo

        file = self.env['patient.document'].sudo().create({
            'res_id': self._origin.id,
            'res_model': 'hms.treatment',
            'name': 'Photo After',
            'display_type': 'after',
            'file_display': photo
        })
        file_type = self.detect_file_type(photo)

        if 'pdf' in file_type.lower():
            file.instruction_pdf = photo
            file.instruction_type = 'pdf'
        else:
            file.datas = photo
            file.instruction_type = 'image'
        attachment_ids = self.attachment_ids.filtered(
            lambda x: x.display_type == "after"
        ).ids
        attachment_ids.append(file.id)
        self.attachment_copy_ids = [(6, 0, attachment_ids)]
        self.attachment_ids = self.attachment_copy_ids
        return file

    def upload_file_before(self, photo_before=False):
        if not photo_before:
            photo = self.photo_before

        file = self.env['patient.document'].sudo().create({
            'res_id': self._origin.id,
            'res_model': 'hms.treatment',
            'name': 'Photo Before',
            'display_type': 'before',
            'file_display': photo
        })
        file_type = self.detect_file_type(photo)

        if 'pdf' in file_type.lower():
            file.instruction_pdf = photo
            file.instruction_type = 'pdf'
        else:
            file.datas = photo
            file.instruction_type = 'image'
        attachment_ids = self.attachment_before_ids.filtered(
            lambda x: x.display_type == "before"
        ).ids
        attachment_ids.append(file.id)
        self.attachment_before_copy_ids = [(6, 0, attachment_ids)]
        self.attachment_before_ids = self.attachment_before_copy_ids
        return file

    def detect_file_type(self, file_content):
        file_type = magic.from_buffer(base64.b64decode(file_content))
        return file_type

    @api.depends('nurse_id')
    def _compute_employee_id(self):
        for line in self:
            line.employee_id = False
            if line.nurse_id:
                line.employee_id = self.env['hr.employee'].search([('user_id', '=', line.nurse_id.id)], limit=1)

    def action_unlink(self):
        self.ensure_one()
        appointment_id = self.appointment_id.id
        self.unlink()
        return {'name': f"Appointment",
                'view_mode': 'form',
                'res_model': 'hms.appointment',
                'view_id': self.env.ref('acs_hms.view_hms_appointment_form').id,
                'res_id': appointment_id,
                'type': 'ir.actions.act_window',
                }

    @api.depends('patient_id')
    def _compute_available_prescription_ids(self):
        for rec in self:
            rec.available_prescription_ids = self.env['prescription.order'].search([
                ('patient_id', '=', rec.patient_id.id),
                ('state', '=', 'prescription')]
            )

    @api.onchange('prescription_ids')
    def onchange_prescription_ids(self):
        for rec in self:
            rec.medicine_line_ids = False
            prescription_line_ids = rec.prescription_ids.mapped('prescription_line_ids')
            for line in prescription_line_ids:
                if line.repeat > 0:
                    rec.medicine_line_ids = [(0, 0, {
                        'product_id': line.product_id.id,
                        'medicine_area_id': line.medicine_area_id.id if line.medicine_area_id else False,
                        'medicine_technique_id': line.medicine_technique_id.id if line.medicine_technique_id else False,
                        'medicine_depth_id': line.medicine_depth_id.id if line.medicine_depth_id else False,
                        'medicine_method_id': line.medicine_method_id.id if line.medicine_method_id else False,
                        'medicine_amount': line.medicine_amount.id if line.medicine_amount else False,
                        'repeat': line.repeat,
                        'prescription_id': line.prescription_id.id,
                    })]

    @api.model
    def default_get(self, fields):
        res = super(ACSTreatment, self).default_get(fields)
        if self._context.get('acs_department_type'):
            department = self.env['hr.department'].search(
                [('department_type', '=', self._context.get('acs_department_type'))], limit=1)
            if department:
                res['department_id'] = department.id
        return res

    def action_view_patient_procedures(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_procedure")
        action['domain'] = [('id', 'in', self.patient_procedure_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id,
                             'default_department_id': self.department_id.id}
        return action

    @api.onchange('department_id')
    def onchange_department(self):
        if self.department_id:
            self.department_type = self.department_id.department_type

    # @api.onchange('template_id')
    # def onchange_template_id(self):
    #     self.finding = None
    #     if self.template_id:
    #         self.finding = self.template_id.notes

    @api.depends('template_ids')
    def _compute_finding(self):
        self.finding = ''
        for rec in self:
            if rec.template_ids:
                for template in rec.template_ids:
                    rec.finding += '\n' + template.notes

    @api.onchange('template_ids')
    def _onchange_finding(self):
        # from bs4 import BeautifulSoup
        for rec in self:
            rec.finding = ''
            if rec.template_ids:
                for template in rec.template_ids:
                    rec.finding += '\n' + template.notes

    def get_line_data(self, line):
        base_date = fields.Date.today()
        return {
            'product_id': line.product_id.id,
            'patient_id': self.patient_id.id,
            'date': fields.datetime.now() + timedelta(days=line.days_to_add),
            'date_stop': fields.datetime.now() + timedelta(days=line.days_to_add) + timedelta(
                hours=line.product_id.procedure_time)
        }

    @api.onchange('procedure_group_id')
    def onchange_procedure_group(self):
        patient_procedure_ids = []
        if self.procedure_group_id:
            for line in self.procedure_group_id.line_ids:
                patient_procedure_ids.append((0, 0, self.get_line_data(line)))
            self.patient_procedure_ids = patient_procedure_ids

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('name', 'New Treatment') == 'New Treatment':
                values['name'] = self.env['ir.sequence'].next_by_code('hms.treatment') or 'New Treatment'
        return super().create(vals_list)

    def unlink(self):
        for data in self:
            if data.state in ['done']:
                raise UserError(('You can not delete record in done state'))
        return super(ACSTreatment, self).unlink()

    def treatment_draft(self):
        self.state = 'draft'

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        self.age = self.patient_id.age

    def treatment_running(self):
        patient_disease_id = self.env['hms.patient.disease'].create({
            'patient_id': self.patient_id.id,
            'treatment_id': self.id,
            'disease_id': self.diagnosis_id.id,
            'age': self.age,
            'diagnosed_date': self.date,
            'healed_date': self.healed_date,
            'allergy_type': self.allergy_type,
            'is_infectious': self.is_infectious,
            'status': self.disease_status,
            'disease_severity': self.disease_severity,
            'lactation': self.lactation,
            'pregnancy_warning': self.pregnancy_warning,
            'is_allergy': self.is_allergy,
            'description': self.description,
        })
        self.patient_disease_id = patient_disease_id.id
        self.state = 'running'

    def treatment_done(self):
        self.state = 'done'
        self.appointment_prescription_line_id.is_done = True
        self.appointment_prescription_line_id.done_at = datetime.now()
        self.appointment_prescription_line_id.prescription_line_id.is_done = True
        self.appointment_prescription_line_id.prescription_line_id.done_at = datetime.now()
        if self.env.context.get('from_appointment'):
            self.appointment_id.write({'state': 'to_after_care'})
            return {'name': f"Appointment",
                    'view_mode': 'form',
                    'res_model': 'hms.appointment',
                    'view_id': self.env.ref('acs_hms.view_hms_appointment_form').id,
                    'res_id': self.appointment_id.id,
                    'type': 'ir.actions.act_window',
                    }

    def treatment_cancel(self):
        self.state = 'cancel'

    def create_order(self):
        product_data = []
        order_data = {
            'date_order': datetime.now(),
            'partner_id': self.patient_id.partner_id.id,
            'user_id': self.env.user.id,
            'state': 'draft',
        }

        order = self.env['sale.order'].create(order_data)
        if not self.medicine_line_ids:
            raise UserError(_("There is no medicine to order."))

        # product_data = self.acs_appointment_inv_product_data()
        if order:
            if self.medicine_line_ids:
                for line in self.medicine_line_ids:
                    product_data.append({
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        # 'pack_lot_ids': [[0, 0, line.acs_lot_id or []]],
                        'order_id': order.id,
                        'product_uom_qty': 1.0,
                        'price_unit': line.product_id.list_price,
                        # 'price_subtotal': 1.0 * line.product_id.list_price,
                        # 'price_subtotal_incl': 0.0
                        # 'name': line.product_id.id
                    })

            if self.consumable_line_ids:
                # product_data.append({
                #     'name': _("Consumed Product/services"),
                # })
                for consumable in self.consumable_line_ids:
                    product_data.append({
                        'product_id': consumable.product_id.id,
                        'name': consumable.product_id.name,
                        'product_uom_qty': consumable.qty,
                        'price_unit': consumable.price_unit,
                        'product_uom': consumable.product_uom_id.id,
                        'order_id': order.id,
                        # 'name': consumable.product_id.id
                    })

        self.env['sale.order.line'].create(product_data)
        self.order_id = order.id

    # def action_appointment(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
    #     action['domain'] = [('treatment_id', '=', self.id)]
    #     action['context'] = {
    #         'default_treatment_id': self.id,
    #         'default_patient_id': self.patient_id.id,
    #         'default_physician_id': self.physician_id.id,
    #         'default_department_id': self.department_id and self.department_id.id or False}
    #     return action

    def action_appointment(self):
        return {'name': f"Appointment",
                'view_mode': 'form',
                'res_model': 'hms.appointment',
                'view_id': self.env.ref('acs_hms.view_hms_appointment_form').id,
                'res_id': self.appointment_id.id,
                'type': 'ir.actions.act_window',
                }

    def create_invoice(self):
        product_id = self.registration_product_id or self.env.user.company_id.treatment_registration_product_id
        acs_context = {'commission_partner_ids': self.physician_id.partner_id.id}
        product_data = []
        if self.medicine_line_ids:
            for line in self.medicine_line_ids:
                product_data.append({
                    'product_id': line.product_id
                })
        if self.consumable_line_ids:
            for consumable in self.consumable_line_ids:
                product_data.append({
                    'product_id': consumable.product_id,
                    'quantity': consumable.qty,
                    'lot_id': consumable.lot_id and consumable.lot_id.id or False,
                })
        # if not product_id:
        #     raise UserError(_("Please Configure Registration Product in Configuration first."))
        invoice = self.with_context(acs_context).acs_create_invoice(partner=self.patient_id.partner_id,
                                                                    patient=self.patient_id,
                                                                    product_data=product_data,
                                                                    inv_data={'hospital_invoice_type': 'treatment'})
        self.invoice_id = invoice.id

    def action_create_procedure_invoice(self):
        procedure_ids = self.patient_procedure_ids.filtered(lambda proc: not proc.invoice_id)
        if not procedure_ids:
            raise UserError(_("There is no Procedure to Invoice or all are already Invoiced."))

        product_data = []
        for procedure in procedure_ids:
            product_data.append({
                'product_id': procedure.product_id,
                'price_unit': procedure.price_unit,
            })

            for consumable in procedure.consumable_line_ids:
                product_data.append({
                    'product_id': consumable.product_id,
                    'quantity': consumable.qty,
                    'lot_id': consumable.lot_id and consumable.lot_id.id or False,
                })
        inv_data = {
            'physician_id': self.physician_id and self.physician_id.id or False,
        }
        invoice = self.acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id,
                                          product_data=product_data, inv_data=inv_data)
        procedure_ids.write({'invoice_id': invoice.id})

    def view_invoice(self):
        invoices = self.invoice_id + self.patient_procedure_ids.mapped('invoice_id')
        action = self.acs_action_view_invoice(invoices)
        action['context'].update({
            'default_partner_id': self.patient_id.partner_id.id,
            'default_patient_id': self.id,
        })
        return action

    def acs_select_treatement_for_appointment(self):
        if self._context.get('acs_current_appointment'):
            # Check if we can get back to appointment in breadcrumb.
            appointment = self.env['hms.appointment'].search(
                [('id', '=', self._context.get('acs_current_appointment'))])
            appointment.treatment_ids = [(6, 0, [self.id])]
            action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
            action['res_id'] = appointment.id
            action['views'] = [(self.env.ref('acs_hms.view_hms_appointment_form').id, 'form')]
            return action
        else:
            raise UserError(_("Something went wrong! Plese Open Appointment and try again"))

    def action_link_patient(self):
        config_action = self.sudo().env.ref("acs_hms_base.action_patient")
        url = "/web#id={}&view_type=kanban&model=hms.patient&action={}".format(
            self.id, config_action and config_action.id or ""
        )
        return {
            'type': 'ir.actions.act_url',
            'name': "Patients",
            'target': 'self',
            'url': url
        }


class TreatmentMedicineLine(models.Model):
    _name = 'treatment.medicine.line'
    _description = "Treatment Medicine Line"
    _order = "sequence"

    name = fields.Char(string='Description')
    sequence = fields.Integer("Sequence", default=10)
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Medicine',
                                 domain=[('hospital_product_type', '=', 'medicament')], required=True)
    medicine_area = fields.Selection([
        ('pre-area', 'Pre-AArea'),
        ('cheek', 'Cheek'),
        ('lips', 'Lips'),
        ('chin', 'Chin'),
        ('alar', 'Alar'),
        ('marionettes', 'Marionettes'),
        ('accordion', 'Accordion lines'),
        ('forehead', 'Forehead'),
        ('peri-oral', 'Peri-Oral'),
        ('tear-trough', 'Tear-Trough'),
        ('peri-orbital', 'Peri-Orbital'),
        ('skinbooster', 'Skinbooster'),
        ('nose', 'Nose'),
        ('ear-lobe', 'Ear-lobe'),
        ('neck', 'Neck'),
        ('hands', 'Hands'),
        ('body', 'Body'),
        ('glabella', 'Glabella'),
        ('frontalis', 'Frontalis'),
        ('LCL', 'LCL'),
        ('nasalis', 'Nasalis'),
        ('LLSAN', 'LLSAN'),
        ('oris', 'O.Oris'),
        ('DAOs', 'DAOs'),
        ('mentalis', 'Mentalis'),
        ('platysma', 'Platysma'),
        ('masseters', 'Masseters'),
        ('micro-tox', 'Micro-tox'),
        ('other', 'Other'),
    ], default='pre-area', string="Area")
    amount = fields.Char(string='Amount')
    acs_lot_id = fields.Many2one("stock.lot",
                                 domain="[('product_id', '=', product_id),'|',('expiration_date','=',False),('expiration_date', '>', context_today().strftime('%Y-%m-%d'))]",
                                 string="Lot/Serial number")

    expiration_date = fields.Datetime(related='acs_lot_id.expiration_date', string='Expiry date')
    # batch_number = fields.Char(string='Batch Number')
    medicine_technique = fields.Selection([
        ('bolus', 'Bolus'),
        ('micro-bolus', 'Micro-Bolus'),
        ('aliquot', 'Aliquot'),
        ('retrograde', 'Retrograde thread'),
        ('anterograde', 'Anterograde thread'),
        ('julie', 'Julie'),
        ('russian', 'Russian')], default='bolus', string='Technique')
    medicine_depth = fields.Selection([
        ('subdermal', 'Subdermal'),
        ('subcutaneous', 'Subcutaneous'),
        ('preperiosteal', 'Preperiosteal'),
        ('intramus', 'Intramuscular')], default='subdermal', string='Depth')

    medicine_method = fields.Selection([
        ('sharp', 'Sharp needle'),
        ('cannula', 'Cannula'),
        ('slip', 'Slip'),
        ('micro', 'Micro-needling'),
        ('dermal', 'Dermal puncture')], default='sharp', string='Method')

    medicine_amount = fields.Many2one('medicine.amount', string='Dose')
    medicine_area_id = fields.Many2one('medicine.area', string="Area")
    medicine_technique_id = fields.Many2one('medicine.technique', string='Technique')
    medicine_depth_id = fields.Many2one('medicine.depth', string='Depth')
    medicine_method_id = fields.Many2one('medicine.method', string='Method')

    treatment_id = fields.Many2one('hms.treatment', string='Treatment')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Clinic',
                                 related='treatment_id.company_id')

    appointment_id = fields.Many2one('hms.appointment', related='treatment_id.appointment_id', string='Appointment')
    repeat = fields.Integer(string='Repeat', default=1)
    prescription_id = fields.Many2one('prescription.order', string='Prescription')

    # qty_available_today = fields.Float(compute='_compute_qty_at_date')
    # qty_to_deliver = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    # free_qty_today = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    forecast_availability = fields.Float('Forecast Availability', compute='_compute_forecast_information',
                                         digits='Product Unit of Measure', compute_sudo=True)
    is_red = fields.Boolean(default=False)
    colour_forecast = fields.Char(string="Color", default="#008000")

    @api.depends('product_id', 'acs_lot_id', 'amount')
    def _compute_forecast_information(self):
        for line in self:
            line.forecast_availability = 0.0
            line.is_red = False
            line.colour_forecast = "#008000"
            if line.acs_lot_id:
                line.forecast_availability = line.acs_lot_id.product_qty
                if line.forecast_availability < float(line.amount):
                    line.is_red = True
                    line.colour_forecast = "#FF0000"

    # @api.depends('product_id', 'amount')
    # def _compute_qty_at_date(self):
    #     print('ok')
    #     for line in self:
    #         line.qty_available_today = 1000
    #         line.free_qty_today = 100
    #         line.qty_to_deliver = float(line.amount)

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {'domain': {'acs_lot_id': [('product_id', '=', self.product_id.id), '|',
                                            ('expiration_date', '=', False),
                                            ('expiration_date', '>', datetime.now().strftime('%Y-%m-%d'))]}}
        return result

    def _openReport(self):
        return


class Medicinearea(models.Model):
    _name = "medicine.area"
    _description = "medicine area"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)


class Medicinetechnique(models.Model):
    _name = "medicine.technique"
    _description = "medicine technique"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)


class Medicinedepth(models.Model):
    _name = "medicine.depth"
    _description = "medicine depth"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)


class Medicinemethod(models.Model):
    _name = "medicine.method"
    _description = "medicine method"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)


class Medicineamount(models.Model):
    _name = "medicine.amount"
    _description = "medicine amount"
    _rec_name = 'name'

    name = fields.Char(string='Amount', required=True)


class TreatmentTemplate(models.Model):
    _name = "treatment.template"
    _description = "Treatment Template"
    _rec_name = 'name'
    _order = 'sequence ASC'

    name = fields.Char(string='Title', required=True)
    sequence = fields.Integer(default=10)
    notes = fields.Html(string='Treatment Note', required=True)


class TreatmentPhotos(models.Model):
    _name = "treatment.photos"
    _description = "Treatment Photos"

    name = fields.Char(string='Title', required=True)
    attachment_before_ids = fields.Many2many('ir.attachment', 'photos_attachment_before_rel', 'attachment_id',
                                             'photos_id', string='Before')
    attachment_after_ids = fields.Many2many('ir.attachment', 'photos_attachment_after_rel', 'attachment_id',
                                            'photos_id', string='After')
    treatment_id = fields.Many2one('hms.treatment', string='Treatment')


class TreatmentPhotosTemplate(models.Model):
    _name = "treatment.photos.template"
    _description = "Treatment Photos Template"

    name = fields.Char(string='Name', required=True)

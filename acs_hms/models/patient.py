# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import time
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import format_datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF, \
    format_datetime as tool_format_datetime

import logging

_logger = logging.getLogger(__name__)
from odoo import exceptions


class ACSPatient(models.Model):
    _inherit = 'hms.patient'

    firstname = fields.Char("First name", index=True)
    lastname = fields.Char("Last name", index=True)
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True,
        readonly=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)

        for vals in vals_list:
            name = vals.get("name", context.get("default_name"))

            if name is not None:
                # Calculate the splitted fields
                inverted = self._get_inverse_name(
                    self._get_whitespace_cleaned_name(name)
                )
                for key, value in inverted.items():
                    if not vals.get(key) or context.get("copy"):
                        vals[key] = value

                # Remove the combined fields
                if "name" in vals:
                    del vals["name"]
                if "default_name" in context:
                    del context["default_name"]
        # pylint: disable=W8121

        res = super(ACSPatient, self.with_context(context)).create(vals_list)
        if 'appointment_id' in context:
            appointment = self.env['hms.appointment'].search([('id', '=', context.get("appointment_id"))], limit=1)
            if appointment:
                appointment.patient_id = res.id if res else False
        return res

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super().default_get(fields_list)

        inverted = self._get_inverse_name(
            self._get_whitespace_cleaned_name(result.get("name", "")))

        for field in list(inverted.keys()):
            if field in fields_list:
                result[field] = inverted.get(field)

        return result

    @api.model
    def _names_order_default(self):
        return "first_last"

    @api.model
    def _get_names_order(self):
        """Get names order configuration from system parameters.
        You can override this method to read configuration from language,
        country, company or other"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_names_order", self._names_order_default())
        )

    @api.model
    def _get_computed_name(self, lastname, firstname):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        order = self._get_names_order()
        if order == "last_first_comma":
            return ", ".join(p for p in (lastname, firstname) if p)
        elif order == "first_last":
            return " ".join(p for p in (firstname, lastname) if p)
        else:
            return " ".join(p for p in (lastname, firstname) if p)

    @api.depends("firstname", "lastname")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        for record in self:
            record.name = record._get_computed_name(record.lastname, record.firstname)

    def _inverse_name_after_cleaning_whitespace(self):
        """Clean whitespace in :attr:`~.name` and split it.

        The splitting logic is stored separately in :meth:`~._inverse_name`, so
        submodules can extend that method and get whitespace cleaning for free.
        """
        for record in self:
            # Remove unneeded whitespace
            clean = record._get_whitespace_cleaned_name(record.name)
            record.name = clean
            record._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name, comma=False):
        """Remove redundant whitespace from :param:`name`.

        Removes leading, trailing and duplicated whitespace.
        """
        if isinstance(name, bytes):
            # With users coming from LDAP, name can be a byte encoded string.
            # This happens with FreeIPA for instance.
            name = name.decode("utf-8")

        try:
            name = " ".join(name.split()) if name else name
        except UnicodeDecodeError:
            # with users coming from LDAP, name can be a str encoded as utf-8
            # this happens with ActiveDirectory for instance, and in that case
            # we get a UnicodeDecodeError during the automatic ASCII -> Unicode
            # conversion that Python does for us.
            # In that case we need to manually decode the string to get a
            # proper unicode string.
            name = " ".join(name.decode("utf-8").split()) if name else name

        if comma:
            name = name.replace(" ,", ",")
            name = name.replace(", ", ",")
        return name

    @api.model
    def _get_inverse_name(self, name):
        """Compute the inverted name.

        - If the partner is a company, save it in the lastname.
        - Otherwise, make a guess.

        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes

        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """

        order = self._get_names_order()
        # Remove redundant spaces
        name = self._get_whitespace_cleaned_name(
            name, comma=(order == "last_first_comma")
        )
        parts = name.split("," if order == "last_first_comma" else " ", 1)
        if len(parts) > 1:
            if order == "first_last":
                parts = [" ".join(parts[1:]), parts[0]]
            else:
                parts = [parts[0], " ".join(parts[1:])]
        else:
            while len(parts) < 2:
                parts.append(False)
        return {"lastname": parts[0], "firstname": parts[1]}

    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        for record in self:
            parts = record._get_inverse_name(record.name)
            record.lastname = parts["lastname"]
            record.firstname = parts["firstname"]

    @api.constrains("firstname", "lastname")
    def _check_name(self):
        """Ensure at least one name is set."""
        for record in self:
            if not all(record.firstname or record.lastname):
                raise exceptions.EmptyNamesError(record)

    @api.model
    def _install_partner_firstname(self):
        """Save names correctly in the database.

        Before installing the module, field ``name`` contains all full names.
        When installing it, this method parses those names and saves them
        correctly into the database. This can be called later too if needed.
        """
        # Find records with empty firstname and lastname
        records = self.search([("firstname", "=", False), ("lastname", "=", False)])

        # Force calculations there
        # records._inverse_name()
        # _logger.info("%d partners updated installing module.", len(records))

    # Disabling SQL constraint givint a more explicit error using a Python
    # contstraint
    # _sql_constraints = [("check_name", "CHECK( 1=1 )", "Contacts require a name.")]

    def _rec_count(self):
        rec = super(ACSPatient, self)._rec_count()
        Prescription = self.env['prescription.order']
        for rec in self:
            rec.prescription_count = Prescription.search_count([('patient_id', '=', rec.id)])
            rec.treatment_count = len(rec.treatment_ids)
            rec.appointment_count = len(rec.appointment_ids)
            rec.evaluation_count = len(rec.evaluation_ids)
            rec.patient_procedure_count = len(rec.patient_procedure_ids)
            rec.checklist_count = len(
                self.env['survey.user_input.line'].search([('appointment_id.patient_id', '=', rec.id)]))

    def _acs_get_attachemnts(self):
        attachments = super(ACSPatient, self)._acs_get_attachemnts()
        attachments += self.appointment_ids.mapped('attachment_ids')
        return attachments

    @api.depends('name', 'mobile', 'city')
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            mobile = rec.mobile if rec.mobile else "NA"
            city = rec.city if rec.city else "NA"
            display_name = ' - '.join(filter(None, [name, mobile, city]))
            result.append((rec.id, display_name))
        return result

    @api.model
    def _get_service_id(self):
        registration_product = False
        if self.env.user.company_id.patient_registration_product_id:
            registration_product = self.env.user.company_id.patient_registration_product_id.id
        return registration_product

    @api.depends('evaluation_ids.state')
    def _get_last_evaluation(self):
        for rec in self:
            evaluation_ids = rec.evaluation_ids.filtered(lambda x: x.state == 'done')

            if evaluation_ids:
                rec.last_evaluation_id = evaluation_ids[0].id if evaluation_ids else False
            else:
                rec.last_evaluation_id = False

    @api.depends('grpah_data_filter')
    def _patient_evaluation_graph_data(self):
        for rec in self:
            today = fields.Datetime.now()
            domain = [('patient_id', '=', rec.id)]
            if rec.grpah_data_filter == 'today':
                domain += [('date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                           ('date', '<=', today.strftime('%Y-%m-%d 23:59:59'))]
            if rec.grpah_data_filter == 'week':
                domain += [('date', '>=', (today + relativedelta(weeks=-1, days=1, weekday=0))),
                           ('date', '<=', (fields.Datetime.today() + relativedelta(weekday=6)))]
            if rec.grpah_data_filter == 'month':
                domain += [('date', '<', (today + relativedelta(months=1)).strftime('%Y-%m-01')),
                           ('date', '>=', time.strftime('%Y-%m-01'))]

            records = self.env['acs.patient.evaluation'].search(domain, order="date")

            rec.patient_weight_line_graph = json.dumps(
                rec.patient_evaluation_line_graph_datas('weight', records, 'Weight'))
            rec.patient_height_line_graph = json.dumps(
                rec.patient_evaluation_line_graph_datas('height', records, 'Height'))
            rec.patient_temp_line_graph = json.dumps(
                rec.patient_evaluation_line_graph_datas('temp', records, 'Temprature'))
            rec.patient_hr_line_graph = json.dumps(rec.patient_evaluation_line_graph_datas('hr', records, 'Heart Rate'))
            rec.patient_rr_line_graph = json.dumps(rec.patient_evaluation_line_graph_datas('rr', records, 'RR'))
            rec.patient_systolic_bp_line_graph = json.dumps(
                rec.patient_evaluation_line_graph_datas('systolic_bp', records, 'Systolic BP'))
            rec.patient_diastolic_bp_line_graph = json.dumps(
                rec.patient_evaluation_line_graph_datas('diastolic_bp', records, 'Diastolic BP'))
            rec.patient_spo2_line_graph = json.dumps(rec.patient_evaluation_line_graph_datas('spo2', records, 'SpO2'))
            rec.patient_rbs_line_graph = json.dumps(rec.patient_evaluation_line_graph_datas('rbs', records, 'RBS'))

    def patient_evaluation_line_graph_datas(self, field_name, records, rec_name):
        patient_data = []
        for record in records:
            formated_date = format_datetime(self.env, record.date, tz=(self.env.user.tz or "UTC"))
            patient_data.append({'x': formated_date, 'y': record[field_name], 'name': 'Patient %s' % rec_name})

        [patient_graph_title, patient_graph_key] = ['Child %s Growth Chart' % rec_name,
                                                    _('Patient %s Chart' % rec_name)]
        return [
            {'values': patient_data, 'title': patient_graph_title, 'key': patient_graph_key, 'area': False,
             'color': 'green'}
        ]

    def acs_check_cancellation_flag(self):
        acs_flag_days = self.env.user.sudo().company_id.acs_flag_days or 365
        acs_flag_count_limit = self.env.user.sudo().company_id.acs_flag_count_limit or 1
        date_start = fields.Datetime.now() - relativedelta(days=acs_flag_days)
        date_end = fields.Datetime.now()
        for rec in self:
            show_cancellation_warning_flag = False
            cancelled_appointments = self.env['hms.appointment'].sudo().search_count([
                ('date', '>=', date_start),
                ('date', '<=', date_end),
                ('patient_id', '=', rec.id),
                ('state', 'in', ['cancel'])
            ])
            if cancelled_appointments >= acs_flag_count_limit:
                show_cancellation_warning_flag = True
            rec.show_cancellation_warning_flag = show_cancellation_warning_flag
            rec.acs_flag_days = acs_flag_days
            rec.acs_cancelled_appointments = cancelled_appointments

    def get_clinic(self):
        if self.env.user.has_group('acs_hms.group_hms_doctor') and not self.env.user.has_group(
                'acs_hms_base.group_hms_manager'):
            return False
        return self.env.user.department_ids

    def get_checklist(self):
        return self.env['medical.checklist'].search([]) or False

    ref_doctor_ids = fields.Many2many('res.partner', 'rel_doc_pat', 'doc_id',
                                      'patient_id', 'Referring Doctors', domain=[('is_referring_doctor', '=', True)])

    # Diseases
    medical_history = fields.Text(string="Past Medical History")
    patient_diseases_ids = fields.One2many('hms.patient.disease', 'patient_id', string='Treatment')

    # Family Form Tab
    genetic_risks_ids = fields.One2many('hms.patient.genetic.risk', 'patient_id', 'Genetic Risks')
    family_history_ids = fields.One2many('hms.patient.family.diseases', 'patient_id', 'Family Diseases History')
    department_ids = fields.Many2many('hr.department', 'patint_department_rel', 'patient_id', 'department_id',
                                      domain=[('patient_department', '=', True)], default=get_clinic, string='Clinic')

    medication_ids = fields.One2many('hms.patient.medication', 'patient_id', string='Medications')
    ethnic_group_id = fields.Many2one('acs.ethnicity', string='Ethnic group')
    cod_id = fields.Many2one('hms.diseases', string='Cause of Death')
    family_member_ids = fields.One2many('acs.family.member', 'patient_id', string='Family')

    prescription_count = fields.Integer(compute='_rec_count', string='# Prescriptions')
    treatment_ids = fields.One2many('hms.treatment', 'patient_id', 'Treatments')
    treatment_count = fields.Integer(compute='_rec_count', string='# Treatments')
    appointment_count = fields.Integer(compute='_rec_count', string='# Appointments')
    appointment_ids = fields.One2many('hms.appointment', 'patient_id', 'Appointments')
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'patient_medical_alert_rel', 'patient_id', 'alert_id',
                                         string='Medical Alerts')
    registration_product_id = fields.Many2one('product.product', default=_get_service_id, string="Registration Service")
    invoice_id = fields.Many2one("account.move", "Registration Invoice", copy=False)

    evaluation_count = fields.Integer(compute='_rec_count', string='# Evaluations')
    evaluation_ids = fields.One2many('acs.patient.evaluation', 'patient_id', 'Evaluations')

    last_evaluation_id = fields.Many2one("acs.patient.evaluation", string="Last Evaluation",
                                         compute=_get_last_evaluation, readonly=True, store=True)
    weight = fields.Float(related="last_evaluation_id.weight", string='Weight', help="Weight in KG", readonly=True)
    height = fields.Float(related="last_evaluation_id.height", string='Height', help="Height in cm", readonly=True)
    temp = fields.Float(related="last_evaluation_id.temp", string='Temp', readonly=True)
    hr = fields.Integer(related="last_evaluation_id.hr", string='HR', help="Heart Rate", readonly=True)
    rr = fields.Integer(related="last_evaluation_id.rr", string='RR', readonly=True, help='Respiratory Rate')
    systolic_bp = fields.Integer(related="last_evaluation_id.systolic_bp", string="Systolic BP")
    diastolic_bp = fields.Integer(related="last_evaluation_id.diastolic_bp", string="Diastolic BP")
    spo2 = fields.Integer(related="last_evaluation_id.spo2", string='SpO2', readonly=True,
                          help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    rbs = fields.Integer(related="last_evaluation_id.rbs", string='RBS', readonly=True,
                         help='Random blood sugar measures blood glucose regardless of when you last ate.')
    bmi = fields.Float(related="last_evaluation_id.bmi", string='Body Mass Index', readonly=True)
    bmi_state = fields.Selection(related="last_evaluation_id.bmi_state", string='BMI State', readonly=True)

    pain_level = fields.Selection(related="last_evaluation_id.pain_level", string="Pain Level", readonly=True)
    pain = fields.Selection(related="last_evaluation_id.pain", string="Pain", readonly=True)

    grpah_data_filter = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('year', 'This Year'),
        ('all', 'All'),
    ], "Grpah Filter Type", default="month")
    patient_weight_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_height_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_temp_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_hr_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_rr_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_systolic_bp_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_diastolic_bp_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_spo2_line_graph = fields.Text(compute='_patient_evaluation_graph_data')
    patient_rbs_line_graph = fields.Text(compute='_patient_evaluation_graph_data')

    acs_weight_name = fields.Char(related="last_evaluation_id.acs_weight_name",
                                  string='Patient Weight unit of measure label')
    acs_height_name = fields.Char(related="last_evaluation_id.acs_height_name",
                                  string='Patient Height unit of measure label')
    acs_temp_name = fields.Char(related="last_evaluation_id.acs_temp_name", string='Patient Temp unit of measure label')
    acs_spo2_name = fields.Char(related="last_evaluation_id.acs_spo2_name", string='Patient SpO2 unit of measure label')
    acs_rbs_name = fields.Char(related="last_evaluation_id.acs_rbs_name", string='Patient RBS unit of measure label')

    patient_procedure_ids = fields.One2many('acs.patient.procedure', 'patient_id', 'Patient Procedures')
    patient_procedure_count = fields.Integer(compute='_rec_count', string='# Patient Procedures')
    show_cancellation_warning_flag = fields.Boolean(compute='acs_check_cancellation_flag',
                                                    string='Show Cancellation Flag')
    acs_flag_days = fields.Integer(compute='acs_check_cancellation_flag', string='Flag Days')
    acs_cancelled_appointments = fields.Integer(compute='acs_check_cancellation_flag', string='Cancelled Appointments')

    is_patient_valid_prescription = fields.Boolean("Valid", compute='_check_valid')
    checklist_count = fields.Integer(compute='_rec_count', string='Medical Checklist')

    question_ids = fields.Many2many('medical.checklist', 'medical_checklist_rel', 'question_id',
                                    'patient_id', string="Medical Checklist", default=get_checklist)

    answer_ids = fields.One2many('patient.medical.checklist.line', 'patient_id', string="Medical Questionnaire")

    is_add_note = fields.Boolean('Is add notes', compute='_compute_is_add_note')

    @api.depends('answer_ids')
    def _compute_is_add_note(self):
        for record in self:
            record.is_add_note = False
            if len(record.answer_ids) > 0:
                answers = record.answer_ids.filtered(lambda x: x.display_type != 'line_note')
                last_answer = answers[-1]
                record.is_add_note = last_answer.yes

    @api.onchange('question_ids')
    def _onchange_question_ids(self):
        lines = []
        for record in self:
            # record.answer_ids = False
            if record.question_ids:
                for checklist in record.question_ids:
                    for line in checklist.detail_ids:
                        if line.checklist_id.id not in lines and line._origin.id not in [a.question_id.id for a in
                                                                                         record.answer_ids]:
                            lines.append((0, 0, {
                                'question_id': line.id,
                                'patient_id': record.id,
                                'checklist_id': line.checklist_id.id
                            }))
            record.answer_ids = lines

    def _check_valid(self):
        Prescription = self.env['prescription.order']
        # condition: 1 search all prescription, 2: 
        for rec in self:
            prescriptions = Prescription.search([('patient_id', '=', rec.id)])
            print("prescriptions", prescriptions)
            if prescriptions:
                valid = []
                for prescription in prescriptions:
                    if prescription.expire_date > fields.Date.today():
                        valid.append(prescription)
                if len(valid) > 0:
                    rec.is_patient_valid_prescription = True
                else:
                    rec.is_patient_valid_prescription = False
            else:
                rec.is_patient_valid_prescription = False

    def action_view_patient_procedures(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_procedure")
        action['domain'] = [('id', 'in', self.patient_procedure_ids.ids)]
        action['context'] = {'default_patient_id': self.id}
        return action

    def today_data(self):
        self.sudo().grpah_data_filter = 'today'

    def week_data(self):
        self.sudo().grpah_data_filter = 'week'

    def month_data(self):
        self.sudo().grpah_data_filter = 'month'

    def year_data(self):
        self.sudo().grpah_data_filter = 'year'

    def all_data(self):
        self.sudo().grpah_data_filter = 'all'

    def show_weight_chart(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_patient_evaluation_graph_1")
        action['domain'] = [('id', '=', self.id)]
        return action

    def create_invoice(self):
        product_id = self.registration_product_id or self.env.user.company_id.patient_registration_product_id
        if not product_id:
            raise UserError(_("Please Configure Registration Product in Configuration first."))

        invoice = self.acs_create_invoice(partner=self.partner_id, patient=self,
                                          product_data=[{'product_id': product_id}],
                                          inv_data={'hospital_invoice_type': 'patient'})
        self.invoice_id = invoice.id

    def create_appointment(self):
        # return the form view of this partner
        self.ensure_one()
        # Get the patient ID
        patient_id = self.id
        # Create a new appointment record
        appointment = self.env['hms.appointment'].create({
            'patient_id': patient_id,
            'department_id': self.env.user.department_ids[0].id if self.env.user.department_ids else False,
            'nurse_id': self.env.user.id,
        })

        # Return the form view of the new appointment record
        return {
            "type": "ir.actions.act_window",
            "res_model": "hms.appointment",
            "res_id": appointment.id,
            "view_mode": "form",
            "view_type": "form",
            "views": [(False, "form")],
            "view_id": False,
            # "target": "new",
        }

    def create_prescription(self):
        # return the form view of this partner
        self.ensure_one()
        # Get the patient ID
        patient_id = self.id
        # Create a new appointment record
        prescription = self.env['prescription.order'].create({
            'patient_id': patient_id,
            'nurse_id': self.env.user.id,
        })

        # Return the form view of the new appointment record
        return {
            "type": "ir.actions.act_window",
            "res_model": "prescription.order",
            "res_id": prescription.id,
            "view_mode": "form",
            "view_type": "form",
            "views": [(False, "form")],
            "view_id": False,
            # "target": "new",
        }

    def action_appointment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_physician_id.id}
        return action

    def action_prescription(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_physician_id.id}
        return action

    def action_treatment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.acs_action_form_hospital_treatment")
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_physician_id.id}
        return action

    def action_evaluation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_evaluation")
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_physician_id.id}
        return action

    def action_view_medical_checklist(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_medical_checklist")
        history_ids = self.env['survey.user_input.line'].search(
            [('appointment_id.patient_id', '=', self.id)])
        action['domain'] = [('id', 'in', history_ids.ids)]
        action['context'] = {'search_default_appointment': 1, 'default_appointment': 1}
        return action


class ACSFamilyMember(models.Model):
    _name = 'acs.family.member'
    _description = 'Family Member'

    related_patient_id = fields.Many2one('hms.patient', string='Family Member', help='Family Member Name',
                                         required=True)
    patient_id = fields.Many2one('hms.patient', string='Patient')
    relation_id = fields.Many2one('acs.family.relation', string='Relation', required=True)
    inverse_relation_id = fields.Many2one("acs.family.member", string="Inverse Relation")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if not record.inverse_relation_id and record.relation_id.inverse_relation_id:
                inverse_relation_id = self.create({
                    'inverse_relation_id': record.id,
                    'relation_id': record.relation_id.inverse_relation_id.id,
                    'patient_id': record.related_patient_id.id,
                    'related_patient_id': record.patient_id.id,
                })
                record.inverse_relation_id = inverse_relation_id.id
        return res

    def unlink(self):
        inverse_relation_id = self.mapped('inverse_relation_id')
        res = super(ACSFamilyMember, self).unlink()
        if inverse_relation_id:
            inverse_relation_id.unlink()
        return res

    def write(self, values):
        res = super(ACSFamilyMember, self).write(values)
        if 'patient_id' in values or 'related_patient_id' in values:
            raise UserError(_("Please Delete Exiting relateion and create new!"))

        if 'relation_id' in values:
            for rec in self:
                if rec.inverse_relation_id and rec.relation_id.inverse_relation_id and rec.relation_id.inverse_relation_id != rec.inverse_relation_id.relation_id:
                    rec.inverse_relation_id.relation_id = rec.relation_id.inverse_relation_id.id
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

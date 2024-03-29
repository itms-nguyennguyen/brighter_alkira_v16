# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from datetime import datetime

import base64
from io import BytesIO


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_referring_doctor = fields.Boolean(string="Is Refereinng Physician")
    # ACS Note: Adding assignee as relation with partner for receptionist or Doctor to access only those patients assigned to them
    assignee_ids = fields.Many2many('res.partner', 'acs_partner_asignee_relation', 'partner_id', 'assigned_partner_id',
                                    domain="[('id','in', suitable_assignee_ids)]", string='Clinician')
    department_id = fields.Many2one('hr.department', string='Clinic')

    suitable_assignee_ids = fields.Many2many('res.partner', compute='_compute_suitable_assignee_ids', precompute=True,
                                             compute_sudo=True)

    is_hide_assignee = fields.Boolean(compute='_compute_is_hide_assignee')

    def _compute_is_hide_assignee(self):
        self.is_hide_assignee = False
        if not self.env.user.has_group('base.group_system'):
            self.is_hide_assignee = True

    def _compute_suitable_assignee_ids(self):
        for record in self:
            nurse_ids = self.env['res.users'].sudo().search(
                [('groups_id', '=', self.env.ref('acs_hms_base.group_hms_manager').id)])
            partner_ids = [user.partner_id.id for user in nurse_ids]
            record.suitable_assignee_ids = self.env['res.partner'].sudo().search([
                ('id', 'in', partner_ids),
            ])

    @api.model_create_multi
    def default_get(self, default_fields):
        res = super(ResPartner, self).default_get(default_fields)
        if self.env.user.department_ids:
            res.update({
                'department_id': self.env.user.department_ids[0].id or False
            })
        return res


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.depends('physician_ids')
    def _compute_physician_count(self):
        for user in self.with_context(active_test=False):
            user.physician_count = len(user.physician_ids)

    def _compute_patient_count(self):
        Patient = self.env['hms.patient']
        for user in self.with_context(active_test=False):
            user.patient_count = Patient.search_count([('partner_id', '=', user.partner_id.id)])

    department_ids = fields.Many2many('hr.department', 'user_department_rel', 'user_id', 'department_id',
                                      domain=[('patient_department', '=', True)], string='Clinic')
    physician_count = fields.Integer(string="#Physician", compute="_compute_physician_count")
    physician_ids = fields.One2many('hms.physician', 'user_id', string='Related Physician')
    patient_count = fields.Integer(string="#Patient", compute="_compute_patient_count")

    # ACS NOTE: On changing the department clearing the cache for the access rights and record rules
    def write(self, values):
        if 'department_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            # self.has_group.clear_cache(self)
        return super(ResUsers, self).write(values)

    @property
    def SELF_READABLE_FIELDS(self):
        user_fields = ['department_ids', 'physician_count', 'physician_ids', 'patient_count']
        return super().SELF_READABLE_FIELDS + user_fields

    @property
    def SELF_WRITEABLE_FIELDS(self):
        user_fields = ['department_ids', 'physician_count', 'physician_ids', 'patient_count']
        return super().SELF_WRITEABLE_FIELDS + user_fields

    def action_create_physician(self):
        self.ensure_one()
        self.env['hms.physician'].create({
            'user_id': self.id,
            'name': self.name,
        })

    def action_create_patient(self):
        self.ensure_one()
        self.env['hms.patient'].create({
            'partner_id': self.partner_id.id,
            'name': self.name,
        })


class HospitalDepartment(models.Model):
    _inherit = 'hr.department'

    note = fields.Text('Note')
    patient_department = fields.Boolean("Patient Department", default=True)
    appointment_ids = fields.One2many("hms.appointment", "department_id", "Appointments")
    department_type = fields.Selection([('general', 'General')], string="Clinic Type")
    consultaion_service_id = fields.Many2one('product.product', ondelete='restrict', string='Consultation Service')
    followup_service_id = fields.Many2one('product.product', ondelete='restrict', string='Followup Service')
    image = fields.Binary(string='Image')
    location_id = fields.Many2one(
        'stock.location', 
        string='Location', 
        help="Location of the department, for stock management purpose.")

class ACSEthnicity(models.Model):
    _description = "Ethnicity"
    _name = 'acs.ethnicity'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    notes = fields.Char(string='Notes')

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Name must be unique!')]


class ACSMedicalAlert(models.Model):
    _name = 'acs.medical.alert'
    _description = "Medical Alert for Patient"

    name = fields.Char(required=True)
    description = fields.Text('Description')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    birthday = fields.Date('Date of Birth')


class ACSFamilyRelation(models.Model):
    _name = 'acs.family.relation'
    _description = "Family Relation"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    inverse_relation_id = fields.Many2one("acs.family.relation", string="Inverse Relation")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.inverse_relation_id:
                name += ' - ' + rec.inverse_relation_id.name
            result.append((rec.id, name))
        return result

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Relation must be unique!')
    ]

    def manage_inverser_relation(self):
        for rec in self:
            if rec.inverse_relation_id and not rec.inverse_relation_id.inverse_relation_id:
                rec.inverse_relation_id.inverse_relation_id = rec.id

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.manage_inverser_relation()
        return res

    def write(self, values):
        res = super(ACSFamilyRelation, self).write(values)
        self.manage_inverser_relation()
        return res


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def get_clinic(self):
        return self.env.user.department_ids

    department_ids = fields.Many2many('hr.department', 'pricelist_department_rel', 'pricelist_id', 'department_id',
                                      default=get_clinic, string='Clinic')


class product_template(models.Model):
    _inherit = "product.template"

    hospital_product_type = fields.Selection(
        selection_add=[('consultation', 'Consultation'), ('pharmacy', 'Pharmacy Products')])
    # ('procedure', 'Procedure'),
    common_dosage_id = fields.Many2one('medicament.dosage', ondelete='cascade',
                                       string='Frequency')
    manual_prescription_qty = fields.Boolean("Manual Prescription Qty")
    procedure_time = fields.Float("Procedure Time")
    appointment_invoice_policy = fields.Selection([('at_end', 'Invoice in the End'),
                                                   ('anytime', 'Invoice Anytime'),
                                                   ('advance', 'Invoice in Advance')],
                                                  string="Appointment Invoicing Policy")
    acs_allow_substitution = fields.Boolean(string='Allow Substitution')
    store_box = fields.Char(string='Store Box')
    generic_name = fields.Char(string='Generic Name')
    company = fields.Char(string='Company')
    lot_no = fields.Char(string='Lot No.')
    batch_no = fields.Char(string='Batch No.')


class ProductProduct(models.Model):
    _inherit = "product.product"

    store_box = fields.Char(string='Store Box')
    generic_name = fields.Char(string='Generic Name')
    company = fields.Char(string='Company')
    lot_no = fields.Char(string='Lot No.')
    batch_no = fields.Char(string='Batch No.')


class ACSConsumableLine(models.Model):
    _inherit = "hms.consumable.line"

    treatment_id = fields.Many2one('hms.treatment', ondelete="cascade", string='Treatment')
    appointment_id = fields.Many2one('hms.appointment', ondelete="cascade", string='Appointment')
    procedure_id = fields.Many2one('acs.patient.procedure', ondelete="cascade", string="Procedure")
    move_ids = fields.Many2many('stock.move', 'consumable_line_stock_move_rel', 'move_id', 'consumable_id',
                                'Kit Stock Moves', readonly=True)
    # ACS: In case of kit moves set move_ids but add move_id also. Else it may lead to comume material process again.


class Physician(models.Model):
    _inherit = 'hms.physician'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.groups_id = [(4, self.env.ref('acs_hms.group_hms_doctor').id)]
        return res

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MedicamentGroupLine(models.Model):
    _name = "medicament.group.line"
    _description = "Medicament Group Line"

    @api.depends('dose', 'days')
    def _get_total_qty(self):
        for rec in self:
            rec.quantity = rec.days * rec.dose

    group_id = fields.Many2one('medicament.group', ondelete='restrict', string='Medicament Group')
    product_id = fields.Many2one('product.product', ondelete='restrict', string='Medicine Name', required=True)
    allow_substitution = fields.Boolean(string='Allow substitution')
    prnt = fields.Boolean(string='Print', help='Check this box to print this line of the prescription.')
    dose = fields.Float(string='Dose', digits=(16, 2), help="Amount of medication (eg, 250 mg) per dose", default=1.0)
    dosage_uom_id = fields.Many2one('uom.uom', string='Unit of Dosage', help='Amount of Medicine (eg, mg) per dose',
                                    domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')
    common_dosage_id = fields.Many2one('medicament.dosage', ondelete='cascade',
                                       string='Dosage Frequency', help='Amount of medication (eg, 250 mg) per dose')
    short_comment = fields.Char(string='Comment', help='Short comment on the specific drug')
    days = fields.Float("Days", default=1.0)
    quantity = fields.Float("Total Qty", compute="_get_total_qty",
                            help="Number of units of the medicament. Example : 30 capsules of amoxicillin", store=True)
    qty_per_day = fields.Float(string='Qty Per Day', default=1.0)
    route_id = fields.Many2one('drug.route', string='Route')

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

    use = fields.Selection([('Stat', 'Stat'), ('3', '3 months'), ('6', '6 months'), ('12', '12 months')],
                           string="Expiration", help="")
    repeat = fields.Integer(string='Repeat', default=5)

    medicine_area_id = fields.Many2one('medicine.area', string="Area")
    medicine_technique_id = fields.Many2one('medicine.technique', string='Technique')
    medicine_depth_id = fields.Many2one('medicine.depth', string='Depth')
    medicine_method_id = fields.Many2one('medicine.method', string='Method')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.common_dosage_id = self.product_id.common_dosage_id.id
            self.dosage_uom_id = self.product_id.dosage_uom_id.id
            self.quantity = self.dose * self.days
            self.route_id = self.product_id.route_id.id

    @api.onchange('common_dosage_id')
    def onchange_common_dosage(self):
        if self.common_dosage_id:
            self.qty_per_day = self.common_dosage_id.qty_per_day


class ACSMedicamentGroup(models.Model):
    _name = "medicament.group"
    _description = "Medicament Group"
    _rec_name = 'name'

    name = fields.Char(string='Group Name', required=True)
    physician_id = fields.Many2one('hms.physician', ondelete='set null', string='Physician')
    diseases_id = fields.Many2one('hms.diseases', ondelete='set null', string='Diseases')
    medicament_group_line_ids = fields.One2many('medicament.group.line', 'group_id', string='Medicament line')
    limit = fields.Integer('Limit')
    active = fields.Boolean(string="Active", default=True)


class ACSMedicationDosage(models.Model):
    _name = 'medicament.dosage'
    _description = "Medicament Dosage"
    _rec_name = 'abbreviation'

    name = fields.Char(translate=True)
    abbreviation = fields.Char(string='Frequency', help='Dosage abbreviation, such as tid in the US or tds in the UK')
    qty_per_day = fields.Float(string='Total Qty Per Day', default=1.0)
    days = fields.Float("Days", default=1.0)
    code = fields.Char(size=8, string='Code', help='Dosage Code,for example: SNOMED 229798009 = 3 times per day')

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Name must be unique!')]


class ACSPatientMedication(models.Model):
    _name = 'hms.patient.medication'
    _description = "Patient Medication"
    _rec_name = 'patient_id'

    patient_id = fields.Many2one('hms.patient', string='Patient')
    physician_id = fields.Many2one('hms.physician', string='Physician',
                                   help='Physician who prescribed the medicament')
    adverse_reaction = fields.Text(string='Adverse Reactions',
                                   help='Side effects or adverse reactions that the patient experienced')
    notes = fields.Text(string='Extra Info')
    is_active = fields.Boolean(string='Active',
                               help='Check if the patient is currently taking the medication')
    course_completed = fields.Boolean(string='Course Completed')
    product_id = fields.Many2one('product.product', string='Medication')
    discontinued_reason = fields.Char(string='Reason for discontinuation',
                                      help='Short description for discontinuing the treatment')
    discontinued = fields.Boolean(string='Discontinued')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

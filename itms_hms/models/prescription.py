# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class PrescriptionLine(models.Model):
    _inherit = 'prescription.line'

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
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.medicine_area = rec.product_id.medicine_area
                rec.medicine_technique = rec.product_id.medicine_technique
                rec.medicine_depth = rec.product_id.medicine_depth
                rec.medicine_method = rec.product_id.medicine_method
        return 
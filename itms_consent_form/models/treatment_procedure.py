from odoo import models, fields, api

class TreatmentProcedure(models.Model):
    _name = 'treatment.procedure'
    _description = 'Treatment Procedure'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    category_ids = fields.Many2many(
        'bureaucrat.knowledge.document',
        string='Consent Forms', 
        domain=[('category_id.name', '=', 'Consent')])

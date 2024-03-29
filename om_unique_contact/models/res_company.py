# -*- coding: utf-8 -*-
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 OM Apps 
#    Email : omapps180@gmail.com
#################################################

from odoo import api, models, fields, _
from odoo.osv import expression


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    partner_field_ids = fields.Many2many('ir.model.fields','om_res_partner_field_company_rel' ,string='Unique Contact Fields')
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    partner_field_ids = fields.Many2many(related='company_id.partner_field_ids', string='Unique Contact Fields',readonly=False)
    
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

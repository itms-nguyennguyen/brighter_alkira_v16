# -*- coding: utf-8 -*-
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 OM Apps 
#    Email : omapps180@gmail.com
#################################################

from odoo import api, models, fields, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    def check_field_unique(self,field_ids,vals):
        for field in field_ids:
            if vals.get(field.name):
                domain = [(field.name,'=',vals.get(field.name))]
                rec_ids = self.env['res.partner'].search(domain)
                if rec_ids:
                    raise ValidationError(_('%s must be unique in %s.')%(field.field_description, 'Contact'))
        
    @api.model_create_multi
    def create(self,vals):
        company_id = self.env.user.company_id
        if company_id.partner_field_ids:
            for val in vals:
                self.check_field_unique(company_id.partner_field_ids,vals)
        return super(ResPartner,self).create(vals)
        
    def write(self,vals):
        company_id = self.env.user.company_id
        if company_id.partner_field_ids:
            self.check_field_unique(company_id.partner_field_ids,vals)
        return super(ResPartner,self).write(vals)
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

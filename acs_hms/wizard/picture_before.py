# coding: utf-8

from odoo import models, api, fields

class TakePictureBefore(models.TransientModel):
    _name = 'hms.picture.before.wizard'
    _description = "Process Done"

    name = fields.Char()
    attachment_ids = fields.Many2many('ir.attachment', string='Take photos')
    appointment_id = fields.Many2one("hms.appointment")

    def button_complete():
        #save
        pass 

    def do_new_treatment(self):
        return {
            'name': f"Do Treatment",
            'view_mode': 'form',
            'res_model': 'hms.treatment',
            'view_id': self.env.ref('acs_hms.view_hospital_hms_treatment_form').id,        
            'res_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {},
        }


class TakePictureAfter(models.TransientModel):
    _name = 'hms.picture.after.wizard'
    _description = "Process Done"

    name = fields.Char()
    attachment_ids = fields.Many2many('ir.attachment', string='Take photos')
    appointment_id = fields.Many2one("hms.appointment")

    def button_complete():
        pass 


# class TreatmentNote(models.TransientModel):

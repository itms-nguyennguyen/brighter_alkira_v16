# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import base64

class AcsImageZoom(http.Controller):

    @http.route(['/my/acs/image/<string:model>/<int:record>'], type='http', auth="user", website=True, sitemap=False)
    def acs_image_preview(self, model=False, record=False, **kwargs):
        record_obj = request.env[model].browse([record])
        # attachments = request.env['patient.document'].search([
        #     ('id', 'in', record_obj.attachment_ids.ids),
        #     ('mimetype', 'in', ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']),
        # ])

        # Fetch related prescription orders
        prescriptions = request.env['prescription.order'].search([('patient_id', '=', record_obj.patient_id.id)])

        return request.render("acs_documents_preview.acs_image_preview", {
            'attachments': record_obj.attachment_ids.mapped('ir_attachment_id'),
            'record_id': record,
            'patient': record_obj.patient_id,
            'prescriptions': prescriptions, 
        })


    @http.route(['/my/acs/image/<string:model>/<int:record>/update_image'], type='http', auth="user", methods=['POST'], website=True)
    def update_image(self, model, record, **post):
        if 'image_data' in post:
            image_data = post['image_data'].split(',')[1]  # Remove the data URL prefix
            image_data = base64.b64decode(image_data)
            attachment = request.env['ir.attachment'].search([('res_model', '=', model), ('res_id', '=', record)], limit=1)
            if attachment:
                attachment.write({'datas': base64.b64encode(image_data).decode('utf-8')})

        # Redirect back to the original Odoo form view
        return request.redirect('/web#action=25&active_id=%s&model=ir.attachment&view_type=kanban&cids=1&menu_id=281' % record)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

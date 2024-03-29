# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class MultipleConsent(models.TransientModel):
    """Create new wizard model of product list for selection"""
    _name = "multiple.consent"
    _description = 'Multiple Selection'

    document_list_ids = fields.Many2many('document.page', domain=[('type', '=', 'content'), ('parent_id.name', '=', 'Consent')],
                                         string='Consent Form List',
                                         help="")

    bureaucrat_document_list_ids = fields.Many2many('bureaucrat.knowledge.document', domain=[('category_id.name', '=', 'Consent')],
                                         string='Consent Form List',
                                         help="")

    def action_add_line(self):
        """Function for adding all the products to the order line that are
        selected from the wizard"""
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        current_id = self.env['hms.appointment'].browse(active_id)
        lines = []
        for rec in self.bureaucrat_document_list_ids:
            if rec not in current_id.consent_ids.knowledge_id:
                lines.append((0, 0, {
                        'appointment_id': active_id,
                        'knowledge_id': rec.id,
                        'content': rec.document_body_html,
                        # 'name': self.env['ir.sequence'].next_by_code('consent.consent') or 'consent',
                        'patient_id': current_id.patient_id.id,
                        'nurse_id': current_id.nurse_id.id,
                }))
        current_id.consent_ids = lines


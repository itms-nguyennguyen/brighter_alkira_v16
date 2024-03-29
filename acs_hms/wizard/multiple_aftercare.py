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


class MultipleAftercare(models.TransientModel):
    """Create new wizard model of product list for selection"""
    _name = "multiple.aftercare"
    _description = 'Multiple Selection'

    document_list_ids = fields.Many2many('document.page', domain=[('type', '=', 'content'), ('parent_id.name', '=', 'After Care')],
                                         string='Aftercare List',
                                         help="")

    bureaucrat_document_list_ids = fields.Many2many('bureaucrat.knowledge.document',
                                         domain=[('category_id.name', '=', 'After Care')],
                                         string='Aftercare List',
                                         help="")

    def action_add_line(self):
        """Function for adding all the products to the order line that are
        selected from the wizard"""
        active_model = self.env.context.get('active_model')
        lines = []
        if active_model == 'hms.appointment':
            appointment_id = self.env.context.get('active_id')
            current_id = self.env['hms.appointment'].browse(appointment_id)
            for rec in self.bureaucrat_document_list_ids:
                if rec not in current_id.aftercare_ids.knowledge_id:
                    lines.append((0, 0, {
                        'appointment_id': appointment_id,
                        'knowledge_id': rec.id,
                        'content': rec.document_body_html,
                        'name': rec.name
                    }))
        if active_model == 'hms.treatment':
            treatment_id = self.env.context.get('active_id')
            current_id = self.env['hms.treatment'].browse(treatment_id)
            for rec in self.bureaucrat_document_list_ids:
                if rec not in current_id.aftercare_ids.knowledge_id:
                    lines.append((0, 0, {
                        'treatment_id': treatment_id,
                        'knowledge_id': rec.id,
                        'content': rec.document_body_html,
                        'name': rec.name
                    }))

        current_id.aftercare_ids = lines


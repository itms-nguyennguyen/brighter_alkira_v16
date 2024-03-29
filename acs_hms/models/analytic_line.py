# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _domain_project_id(self):
        domain = [('allow_timesheets', '=', True)]
        if not self.user_has_groups('hr_timesheet.group_timesheet_manager'):
            return expression.AND([domain,
                                   ['|', ('privacy_visibility', '!=', 'followers'),
                                    ('message_partner_ids', 'in', [self.env.user.partner_id.id])]
                                   ])
        return domain

    def _get_project_id(self):
        return self.env['project.project'].search([('name', 'ilike', 'CPD')], limit=1)

    def _get_task_id(self):
        return self.env['project.task'].search([('project_id.name', 'ilike', 'CPD')], limit=1)

    description = fields.Text('Description')
    name = fields.Char('Name')
    location = fields.Selection(
        [('online', 'Online'), ('hospital', 'Hospital'), ('seminar', 'Seminar'), ('clinic', 'Clinic')],
        string='Location', default='online')

    attachment_certification_ids = fields.Many2many('ir.attachment', 'certification_attachment_rel', 'attachment_id',
                                                    'analytic_id', string='Certifications')
    certification_expiry = fields.Date('Date Expiry')
    channel_id = fields.Many2one('slide.channel', string="Title", index=True,
                                 ondelete='cascade')

    task_id = fields.Many2one(
        'project.task', string='Task', default=_get_task_id, index='btree_not_null',
        compute='_compute_task_id', store=True, readonly=False,
        domain="[('company_id', '=', company_id), ('project_id.allow_timesheets', '=', True), ('project_id', '=?', project_id)]")

    project_id = fields.Many2one(
        'project.project', 'Project', domain=_domain_project_id, default=_get_project_id, index=True,
        compute='_compute_project_id', store=True, readonly=False)

    department_id = fields.Many2one('hr.department', ondelete='restrict', related='employee_id.department_id',
                                    string='Clinic')

    def unlink(self):
        is_delete = bool(self.env.user.has_group('hr_timesheet.group_timesheet_manager') and self.env.user.id != self.user_id.id and self.project_id)
        for record in self:
            if is_delete:
                raise UserError(_('You are not allowed delete %s record') % record.name or record.channel_id.name)
        return super(AccountAnalyticLine, self).unlink()

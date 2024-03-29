# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from twilio.rest import Client
from odoo.addons.twilio_sms_gateway_gsc.twilio_sms_gateway_gsc_api.twilio_sms_gateway_gsc_api import TwilioSendSMSAPI
import magic
import base64

_logger = logging.getLogger(__name__)

PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
]
RATING = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'Extreme High')
]


class HelpDeskTicket(models.Model):
    """Help_ticket model"""
    _name = 'help.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default=lambda self: self.env['ir.sequence'].
                       next_by_code('help.ticket') or _('New'))
    # customer_id = fields.Many2one('res.partner',
    #                               string='Customer Name',
    #                               help='Customer Name')
    customer_name = fields.Char('Customer Name', help='Customer Name')
    subject = fields.Text('Subject', required=True, store=True,
                          help='Subject of the Ticket', compute="_compute_subject", readonly=False)
    description = fields.Text('Description', required=True,
                              help='Description')
    email = fields.Char('Email', help='Email')
    phone = fields.Char('Phone', help='Contact Number')
    team_id = fields.Many2one('help.team', string='Helpdesk Team',
                              help='Helpdesk Team Name')
    product_id = fields.Many2many('product.template',
                                  string='Product',
                                  help='Product Name')
    # project_id = fields.Many2one('project.project',
    #                              string='Project',
    #                              readonly=False,
    #                              related='team_id.project_id',
    #                              store=True,
    #                              help='Project Name')

    # priority = fields.Selection(PRIORITIES, default='1', help='Priority of the'
    #                                                           ' Ticket')
    stage_name = fields.Char("Stage name", related='stage_id.name')
    stage_id = fields.Many2one('ticket.stage', string='Stage',
                               default=lambda self: self.env[
                                   'ticket.stage'].search(
                                   [('name', '=', 'Draft')], limit=1).id,
                               tracking=True,
                               group_expand='_read_group_stage_ids',
                               help='Stages')
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              check_company=True,
                              index=True, tracking=True,
                              help='Login User')
    cost = fields.Float('Cost per hour', help='Cost Per Unit')
    service_product_id = fields.Many2one('product.product',
                                         string='Service Product',
                                         help='Service Product',
                                         domain=[
                                             ('detailed_type', '=', 'service')])
    create_date = fields.Datetime('Creation Date', help='Created date')
    start_date = fields.Datetime('Start Date', help='Start Date')
    end_date = fields.Datetime('End Date', help='End Date')
    public_ticket = fields.Boolean(string="Public Ticket", help='Public Ticket')
    invoice_ids = fields.Many2many('account.move',
                                   string='Invoices',
                                   help='Invoicing id'
                                   )
    # task_ids = fields.Many2many('project.task',
    #                             string='Tasks',
    #                             help='Task id')
    color = fields.Integer(string="Color", help='Color')
    replied_date = fields.Datetime('Replied date', help='Replied Date')
    last_update_date = fields.Datetime('Last Update Date',
                                       help='Last Update Date')
    ticket_type = fields.Many2one('helpdesk.types',
                                  string='Ticket Type', help='Ticket Type')
    ticket_name = fields.Char('Ticket Name', help='Ticket Name', related='ticket_type.name')
    team_head = fields.Many2one('res.users', string='Team Leader',
                                compute='_compute_team_head',
                                help='Team Leader Name')
    assigned_user = fields.Many2one('res.users',
                                    domain=lambda self: [
                                        ('groups_id', 'in', self.env.ref(
                                            'odoo_website_helpdesk.helpdesk_user').id)],
                                    default=lambda self: self.env.user.id,
                                    help='Assigned User Name')
    category_id = fields.Many2one('helpdesk.categories',
                                  help='Category')
    tags = fields.Many2many('helpdesk.tag', help='Tags')
    assign_user = fields.Boolean(default=False, help='Assign User')

    merge_ticket_invisible = fields.Boolean(string='Merge Ticket',
                                            help='Merge Ticket Invisible or '
                                                 'Not', default=False)
    merge_count = fields.Integer(string='Merge Count', help='Merged Tickets '
                                                            'Count')
    active = fields.Boolean(default=True, help='Active', string='Active')

    customer_id = fields.Many2one('res.partner', related="patient_id.partner_id")
    patient_id = fields.Many2one('hms.patient', string='Patient')
    primary_physician_id = fields.Many2one('hms.physician', string='Prescriber',
                                           related='patient_id.primary_physician_id')
    nurse_id = fields.Many2one('res.users', string='Nurse', default=lambda self: self.env.user.id)
    branch_id = fields.Many2one('hr.department', ondelete="cascade", string='Clinic',
                                default=lambda self: self.env.user.department_ids[0].id)
    allow_department_ids = fields.Many2many('hr.department', string='Allowed Departments',
                                            related='nurse_id.department_ids')
    clinic_manager_id = fields.Many2one('hr.employee', string='Clinic Manager', related='branch_id.manager_id')
    alkira_manager_id = fields.Many2one('hr.employee', readonly='1', string='Alkira Manager',
                                        compute='_compute_alkira_manager_id')
    chemical_burns_event_boolean = fields.Boolean(string='Chemical Burns', default=False)
    medication_error_event_boolean = fields.Boolean(string='Medication Errors', default=False)
    blindness_event_boolean = fields.Boolean(string='Blindness', default=False)
    infections_event_boolean = fields.Boolean(string='Infections', default=False)
    allergic_event_boolean = fields.Boolean(string='Allergic Reactions', default=False)

    vascular = fields.Boolean(string='Vascular', default=False)
    occlusion = fields.Boolean(string='Occlusion', default=False)
    skin = fields.Boolean(string='Skin', default=False)
    necrosis = fields.Boolean(string='Necrosis', default=False)
    granuloma = fields.Boolean(string='Granuloma', default=False)
    ptosis = fields.Boolean(string='Ptosis', default=False)
    odema = fields.Boolean(string='Odema', default=False)
    needle = fields.Boolean(string='Needle', default=False)
    stick = fields.Boolean(string='Stick', default=False)
    injury = fields.Boolean(string='Injury', default=False)
    vasovegal = fields.Boolean(string='Vasovegal', default=False)
    episode = fields.Boolean(string='Episode', default=False)
    bruising = fields.Boolean(string='Bruising', default=False)
    herpetic = fields.Boolean(string='Herpetic', default=False)
    reaction = fields.Boolean(string='Reaction', default=False)
    tyndall = fields.Boolean(string='Tyndall', default=False)
    effect = fields.Boolean(string='Effect', default=False)
    migration = fields.Boolean(string='Migration', default=False)

    is_sent = fields.Boolean(string='Sent', default=False)

    attachment_ids = fields.One2many(
        'patient.document', 'res_id',
        string='Attachments', ondelete='cascade',
        readonly=False
    )
    attachment_copy_ids = fields.Many2many(
        'patient.document', 'ticket_attachment_rel', 'res_id', 'ticket_id', ondelete='cascade',
        string='Attachments',
        readonly=False
    )
    photo = fields.Binary(string='Photo')
    is_invisible = fields.Boolean(compute="_compute_is_invisible")

    @api.depends('attachment_ids')
    def _compute_is_invisible(self):
        for rec in self:
            is_invisible = True
            if rec.attachment_ids:
                is_invisible = False
            rec.is_invisible = is_invisible

    @api.onchange('primary_physician_id')
    def onchange_primary_physician_id(self):
        if self.primary_physician_id:
            self.assign_user = self.primary_physician_id.user_id.id

    @api.onchange('photo')
    def onchange_photo(self):
        if self.photo:
            self.upload_file()
            self.is_invisible = False
            self.photo = False

    @api.onchange('attachment_ids')
    def onchange_attachment_ids(self):
        if not self.attachment_ids:
            self.is_invisible = True

    def upload_file(self, photo=False):
        if not photo:
            photo = self.photo

        file = self.env['patient.document'].sudo().create({
            'res_id': self._origin.id,
            'res_model': 'help.ticket',
            'name': 'Photo',
            'file_display': photo
        })
        file_type = self.detect_file_type(photo)

        if 'pdf' in file_type.lower():
            file.instruction_pdf = photo
            file.instruction_type = 'pdf'
        else:
            file.datas = photo
            file.instruction_type = 'image'
        attachment_ids = self.attachment_ids.ids
        attachment_ids.append(file.id)
        self.attachment_copy_ids = [(6, 0, attachment_ids)]
        self.attachment_ids = self.attachment_copy_ids
        return file

    def detect_file_type(self, file_content):
        file_type = magic.from_buffer(base64.b64decode(file_content))
        return file_type

    def action_add_follower(self):
        self.ensure_one()
        # add prescriber, clinic manager, alkira manager as followers
        parter_ids = []
        if self.primary_physician_id:
            parter_ids.append(self.primary_physician_id.partner_id.id)
        if self.clinic_manager_id:
            parter_ids.append(self.clinic_manager_id.related_contact_ids
                              and self.clinic_manager_id.related_contact_ids[0].id or False)
        if self.alkira_manager_id:
            parter_ids.append(self.alkira_manager_id.related_contact_ids
                              and self.alkira_manager_id.related_contact_ids[0].id or False)
        self.message_subscribe(partner_ids=parter_ids)

    @api.depends('ticket_type')
    def _compute_alkira_manager_id(self):
        alkira_clinic_id = self.env['hr.department'].sudo().name_search('Alkira Aesthetics')
        if not alkira_clinic_id:
            for rec in self:
                rec.alkira_manager_id = False
            return
        manager_id = self.env['hr.department'].sudo().browse(alkira_clinic_id[0][0]).manager_id
        if not manager_id:
            for rec in self:
                rec.alkira_manager_id = False
            return
        for rec in self:
            if rec.ticket_type.name != 'Adverse Event':
                rec.alkira_manager_id = False
                continue
            rec.alkira_manager_id = manager_id.id

    @api.depends('name', 'patient_id', 'patient_id.name', 'ticket_type', 'ticket_type.name')
    def _compute_subject(self):
        for rec in self:
            rec.subject = rec.name or ''
            if rec.patient_id:
                rec.subject += ' - ' + rec.patient_id.name
            if rec.ticket_type:
                rec.subject += ' - ' + rec.ticket_type.name

    @api.onchange(
        'nurse_id', 'patient_id',
        'chemical_burns_event_boolean',
        'medication_error_event_boolean',
        'blindness_event_boolean',
        'infections_event_boolean',
        'allergic_event_boolean',
        'ticket_type')
    def onchange_adverse_event_boolean(self):
        for rec in self:
            rec.description = ''
            if rec.ticket_name != 'Adverse Event':
                continue
            if rec.nurse_id:
                rec.phone = rec.nurse_id.phone

            if rec.chemical_burns_event_boolean == True:
                rec.description += 'Chemical Burns,'

            if rec.medication_error_event_boolean == True:
                rec.description += 'Medication Errors,'

            if rec.blindness_event_boolean == True:
                rec.description += 'Blindness,'

            if rec.infections_event_boolean == True:
                rec.description += 'Infections,'

            if rec.allergic_event_boolean == True:
                rec.description += 'Allergic Reactions'

            rec.description = f'''Urgent - Adverse Event - Please respond urgently
Clinic: {rec.nurse_id.department_ids[0].name}
Nurse: {rec.nurse_id.name}
Patient: {rec.customer_id.name}
Contact: {rec.phone}
Adverse Event: {rec.description}.'''

    def send_sms(self):
        # recipients are list of users
        recipients = []
        self.is_sent = True
        stage_id = self.env['ticket.stage'].search([
            ('name', '=', 'In Progress')
        ], limit=1)
        self.write({'stage_id': stage_id.id})

        value = self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_nurse')
        if self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_nurse'):
            recipients.append(self.nurse_id)
        if self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_clinic_manager'):
            if self.clinic_manager_id.user_id not in recipients:
                recipients.append(self.clinic_manager_id.user_id)
        if self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_brighter_emergency'):
            user_id = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_website_helpdesk.brighter_emergency_contact')
            user = self.env['res.users'].browse(int(user_id))
            if user not in recipients:
                recipients.append(user)

        if self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_sms'):
            twilio_account_id = self.env['twilio.sms.gateway.account'].search([('state', '=', 'confirmed')], limit=1)
            twilio_account_from_number = twilio_account_id.account_from_mobile_number
            message = self.description

            for partner_id in recipients:
                customer_number = partner_id.mobile or partner_id.phone or ""
                formatted_number = customer_number
                if formatted_number.startswith('0'):
                    formatted_number = formatted_number[1:]
                # Adding +61 if the number doesn't start with it
                if not formatted_number.startswith('+61'):
                    formatted_number = '+61' + formatted_number
                datas = {
                    "From": twilio_account_from_number,
                    "To": formatted_number.replace(" ", ""),
                    "Body": message
                }
                result, response = self.send_sms_to_recipients(datas)
                # log to user
                if partner_id:
                    body = f"SMS to {formatted_number}: {message}"
                    message_type = 'sms'
                    partner_id.partner_id.message_post(body=body, type=message_type)
                # log to helpdesk
                if self.id:
                    self.message_post(body=body, type=message_type)
                if not result:
                    break
            pass
        if self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_email'):
            # s end email here
            for partner_id in recipients:
                mail_pool = self.env['mail.mail']
                values = {}
                values.update({
                    'subject': self.name,
                    'email_to': partner_id.partner_id.email,
                    'body_html': self.description
                })
                msg_id = mail_pool.sudo().create(values).send()
                if partner_id:
                    body = f"Emailed to {partner_id.partner_id.email}: {self.description}"
                    message_type = 'email'
                    partner_id.partner_id.message_post(body=body, type=message_type)
                # log to helpdesk
                if self.id:
                    self.message_post(body=body, type=message_type)
            pass
        if self.env['ir.config_parameter'].sudo().get_param('odoo_website_helpdesk.noti_chatter'):
            # send chatter here
            for partner_id in recipients:
                channel = self.env['mail.channel'].channel_get([partner_id.partner_id.id])
                channel_id = self.env['mail.channel'].browse(channel["id"])
                channel_id.message_post(
                    body=self.description,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
                if partner_id:
                    body = f"Noticed to chatter: {self.description}"
                    message_type = 'sms'
                    partner_id.partner_id.message_post(body=body, type=message_type)
                # log to helpdesk
                if self.id:
                    self.message_post(body=body, type=message_type)

    @api.onchange('team_id', 'team_head')
    def team_leader_domain(self):
        """Changing the team leader when selecting the team"""
        li = []
        for rec in self.team_id.member_ids:
            li.append(rec.id)
        return {'domain': {'assigned_user': [('id', 'in', li)]}}

    @api.depends('team_id')
    def _compute_team_head(self):
        """Compute the team head function"""
        self.team_head = self.team_id.team_lead_id.id

    @api.onchange('stage_id')
    def mail_snd(self):
        """Sending mail to the user function"""
        rec_id = self._origin.id
        data = self.env['help.ticket'].search([('id', '=', rec_id)])
        data.last_update_date = fields.Datetime.now()
        if self.stage_id.starting_stage:
            data.start_date = fields.Datetime.now()
        if self.stage_id.closing_stage or self.stage_id.cancel_stage:
            data.end_date = fields.Datetime.now()
        if self.stage_id.template_id:
            mail_template = self.stage_id.template_id
            mail_template.send_mail(self._origin.id, force_send=True)

    def assign_to_teamleader(self):
        """Assigning team leader function"""
        if self.team_id:
            self.team_head = self.team_id.team_lead_id.id
            mail_template = self.env.ref(
                'odoo_website_helpdesk.odoo_website_helpdesk_assign')
            mail_template.sudo().write({
                'email_to': self.team_head.email,
                'subject': self.name
            })
            mail_template.sudo().send_mail(self.id, force_send=True)
        else:
            raise ValidationError("Please choose a Helpdesk Team")

    def _default_show_create_task(self):
        """Task creation"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_create_task')

    # show_create_task = fields.Boolean(string="Create Task",
    #                                   default=_default_show_create_task,
    #                                   compute='_compute_show_create_task')
    # create_task = fields.Boolean(string="Create Task", readonly=False,
    #                              related='team_id.create_task', store=True)
    billable = fields.Boolean(string="Billable", default=False)

    def _default_show_category(self):
        """Show category default"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_category')

    show_category = fields.Boolean(default=_default_show_category,
                                   compute='_compute_show_category')
    customer_rating = fields.Selection(RATING, default='0', readonly=True)

    review = fields.Char('Review', readonly=True)
    kanban_state = fields.Selection([
        ('normal', 'Ready'),
        ('done', 'In Progress'),
        ('blocked', 'Blocked'), ], default='normal')

    def _compute_show_category(self):
        """Compute show category"""
        show_category = self._default_show_category()
        for rec in self:
            rec.show_category = show_category

    # def _compute_show_create_task(self):
    #     """Compute the created task"""
    #     show_create_task = self._default_show_create_task()
    #     for record in self:
    #         record.show_create_task = show_create_task

    def auto_close_ticket(self):
        """Automatically closing the ticket"""
        auto_close = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.auto_close_ticket')
        if auto_close:
            no_of_days = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_website_helpdesk.no_of_days')
            records = self.env['help.ticket'].search([])
            for rec in records:
                days = (fields.Datetime.today() - rec.create_date).days
                if days >= int(no_of_days):
                    close_stage_id = self.env['ticket.stage'].search(
                        [('closing_stage', '=', True)])
                    if close_stage_id:
                        rec.stage_id = close_stage_id

    def default_stage_id(self):
        # Search your stage
        return self.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        return the stages to stage_ids
        """
        stage_ids = self.env['ticket.stage'].search([])
        return stage_ids

    @api.model_create_multi
    def create(self, vals_list):
        """Create function"""
        return super(HelpDeskTicket, self).create(vals_list)

    def write(self, vals):
        """Write function"""
        result = super(HelpDeskTicket, self).write(vals)
        return result

    def create_invoice(self):
        """Create Invoice based on the ticket"""
        # tasks = self.env['project.task'].search(
        #     [('project_id', '=', self.project_id.id),
        #      ('ticket_id', '=', self.id)]).filtered(
        #     lambda line: line.ticket_billed == False)
        # if not tasks:
        #     raise UserError('No Tasks to Bill')

        # total = sum(x.effective_hours for x in tasks if x.effective_hours > 0)

        # invoice_no = self.env['ir.sequence'].next_by_code(
        #     'ticket.invoice')
        # self.env['account.move'].create([
        #     {
        #         'name': invoice_no,
        #         'move_type': 'out_invoice',
        #         'customer_id': self.patient_id.partner_id.id,
        #         'ticket_id': self.id,
        #         'date': fields.Date.today(),
        #         'invoice_date': fields.Date.today(),
        #         'invoice_line_ids': [(0, 0,
        #                               {'product_id': self.service_product_id.id,
        #                                'name': self.service_product_id.name,
        #                                'quantity': total,
        #                                'product_uom_id': self.service_product_id.uom_id.id,
        #                                'price_unit': self.cost,
        #                                'account_id': self.service_product_id.categ_id.property_account_income_categ_id.id,
        #                                })],
        #     }, ])
        # for task in tasks:
        #     task.ticket_billed = True
        # return {
        #     'effect': {
        #         'fadeout': 'medium',
        #         'message': 'Billed Successfully!',
        #         'type': 'rainbow_man',
        #     }
        # }

    def create_tasks(self):
        return
        """Task creation"""
        # task_id = self.env['project.task'].create({
        #     'name': self.name + '-' + self.subject,
        #     'company_id': self.env.company.id,
        #     'ticket_id': self.id,
        # })
        # self.write({
        #     'task_ids': [(4, task_id.id)]
        # })

        # return {
        #     'name': 'Tasks',
        #     'res_model': 'project.task',
        #     'view_id': False,
        #     'res_id': task_id.id,
        #     'view_mode': 'form',
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        # }

    def open_tasks(self):
        return
        # """View the Created task """
        # return {
        #     'name': 'Tasks',
        #     'domain': [('ticket_id', '=', self.id)],
        #     'res_model': 'project.task',
        #     'view_id': False,
        #     'view_mode': 'tree,form',
        #     'type': 'ir.actions.act_window',
        # }

    def open_invoices(self):
        """View the Created invoice"""
        return {
            'name': 'Invoice',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def open_merged_tickets(self):
        """Open the merged tickets tree view"""
        ticket_ids = self.env['support.tickets'].search(
            [('merged_ticket', '=', self.id)])
        # Get the display_name matching records from the support.tickets
        helpdesk_ticket_ids = ticket_ids.mapped('display_name')
        # Get the IDs of the help.ticket records matching the display names
        help_ticket_records = self.env['help.ticket'].search(
            [('name', 'in', helpdesk_ticket_ids)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Ticket',
            'view_mode': 'tree,form',
            'res_model': 'help.ticket',
            'domain': [('id', 'in', help_ticket_records.ids)],
            'context': self.env.context,
        }

    def action_send_reply(self):
        """Action to sent reply button"""
        template_id = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.reply_template_id'
        )
        template_id = self.env['mail.template'].browse(int(template_id))
        if template_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'mail',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'target': 'new',
                'views': [[False, 'form']],
                'context': {
                    'default_model': 'help.ticket',
                    'default_res_id': self.id,
                    'default_template_id': template_id.id
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'mail',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_model': 'help.ticket',
                'default_res_id': self.id,
            }
        }

    def solved(self):
        for line in self:
            stage_id = self.env['ticket.stage'].search([
                ('name', '=', 'Closed')
            ], limit=1)
            line.write({'stage_id': stage_id.id})

    def cancel(self):
        for line in self:
            stage_id = self.env['ticket.stage'].search([
                ('name', '=', 'Canceled')
            ], limit=1)
            line.write({'stage_id': stage_id.id})

    # copy from send sms
    def send_sms_to_recipients(self, datas):
        twilio_sms_log_history_obj = self.env['twilio.sms.log.history']
        twilioSendSMSAPIObj = TwilioSendSMSAPI()
        twilio_account_id = self.env['twilio.sms.gateway.account'].search([('state', '=', 'confirmed')], limit=1)
        # twilio_account_id = self.twilio_account_id
        response_obj = twilioSendSMSAPIObj.post_twilio_sms_send_to_recipients_api(twilio_account_id, datas)
        if response_obj.status_code in [200, 201]:
            response = response_obj.json()
            twilio_sms_log_history_obj.create({
                # 'sms_send_rec_id': self.id,
                'twilio_account_id': twilio_account_id.id,
                'message_id': response.get("sid"),
                'mobile_number': response.get("to"),
                'message': response.get("body"),
                'status': response.get("status"),
                'message_price': response.get("price", 0.0),
            })
        elif response_obj.status_code in [400]:
            response = response_obj.json()
            twilio_sms_log_history_obj.create({
                # 'sms_send_rec_id': self.id,
                'twilio_account_id': twilio_account_id.id,
                'message_id': "",
                'mobile_number': datas.get("To"),
                'message': datas.get("Body"),
                'status': "Error",
                'message_price': 0.0,
                'error_code': response.get('code'),
                'error_message': response.get('message'),
                'error_status_code': response.get('status'),
                'error_more_info': response.get('more_info'),
            })
        elif response_obj.status_code in [401]:
            response = response_obj.json()
            twilio_sms_log_history_obj.create({
                # 'sms_send_rec_id': self.id,
                'twilio_account_id': twilio_account_id.id,
                'message_id': "",
                'mobile_number': datas.get("To"),
                'message': datas.get("Body"),
                'status': "Error",
                'message_price': 0.0,
                'error_code': response.get('code'),
                'error_message': response.get('message'),
                'error_status_code': response.get('status'),
                'error_more_info': response.get('more_info'),
            })
            return False, response
        return True, ""


class StageTicket(models.Model):
    """Stage Ticket class"""
    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'
    _fold_name = 'fold'

    name = fields.Char('Name', help='Name')
    active = fields.Boolean(default=True, help='Active', string='Active')
    sequence = fields.Integer(default=50, help='Sequence', string='Sequence')
    closing_stage = fields.Boolean('Closing Stage', default=False,
                                   help='Closing stage')
    cancel_stage = fields.Boolean('Cancel Stage', default=False,
                                  help='Cancel stage')
    starting_stage = fields.Boolean('Start Stage', default=False,
                                    help='Starting Stage')
    folded = fields.Boolean('Folded in Kanban', default=False,
                            help='Folded Stage')
    template_id = fields.Many2one('mail.template',
                                  help='Templates',
                                  domain="[('model', '=', 'help.ticket')]")
    group_ids = fields.Many2many('res.groups', help='Group ID')
    fold = fields.Boolean(string='Fold', help='Folded')

    def unlink(self):
        """Unlinking Function"""
        for rec in self:
            tickets = rec.search([])
            sequence = tickets.mapped('sequence')
            lowest_sequence = tickets.filtered(
                lambda x: x.sequence == min(sequence))
            if self.name == "Draft":
                raise UserError(_("Cannot Delete This Stage"))
            if rec == lowest_sequence:
                raise UserError(_("Cannot Delete '%s'" % (rec.name)))
            else:
                res = super().unlink()
                return res


class HelpdeskTypes(models.Model):
    """Helpdesk types """
    _name = 'helpdesk.types'
    _description = 'Helpdesk Types'

    name = fields.Char(string='Type', help='Types')


# class Tasks(models.Model):
#     """Inheriting the task"""
#     _inherit = 'project.task'

#     ticket_billed = fields.Boolean('Billed', default=False,
#                                    help='Billed Tickets')


class HelpdeskTags(models.Model):
    """Helpdesk tags"""
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tags'

    name = fields.Char(string='Tag', help='Tag Name')

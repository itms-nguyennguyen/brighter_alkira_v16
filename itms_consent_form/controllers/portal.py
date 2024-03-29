# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii

from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        Consent = request.env['consent.consent']
        if 'consent_count' in counters:
            values['consent_count'] = Consent.search_count(self._prepare_consent_domain(partner)) \
                if Consent.check_access_rights('read', raise_exception=False) else 0

        return values

    def _prepare_consent_domain(self, partner):
        return [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])
        ]

    def _get_consent_searchbar_sortings(self):
        return {
            'date': {'label': _('Signed On'), 'order': 'patient_signed_on desc'},
            'name': {'label': _('Title'), 'order': 'name'}
        }

    def _prepare_consent_form_portal_rendering_values(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kwargs
    ):
        Consent = request.env['consent.consent']

        if not sortby:
            sortby = 'date'

        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        url = "/my/consent-form"
        domain = self._prepare_consent_domain(partner)
        searchbar_sortings = self._get_consent_searchbar_sortings()
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        pager_values = portal_pager(
            url=url,
            total=Consent.search_count(domain),
            page=page,
            step=self._items_per_page,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        )
        consents = Consent.search(domain, order=sort_order, limit=self._items_per_page, offset=pager_values['offset'])
        values.update({
            'date': date_begin,
            'consent_forms': consents.sudo(),
            'page_name': 'consent-form',
            'pager': pager_values,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return values

    @http.route(['/my/consent-form', '/my/consent-form/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_consent_form(self, **kwargs):
        values = self._prepare_consent_form_portal_rendering_values(**kwargs)
        request.session['my_consent_history'] = values['consent_forms'].ids[:100]
        return request.render("itms_consent_form.portal_my_consent_form", values)

    @http.route(['/my/consent-form/<int:consent_id>'], type='http', auth="public", website=True)
    def portal_consent_page(self, consent_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            consent_sudo = self._document_check_access('consent.consent', consent_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=consent_sudo, report_type=report_type,
                                     report_ref='itms_consent_form.action_report_consent', download=download)

        if request.env.user.share and access_token:
            today = fields.Date.today().isoformat()

        backend_url = f'/web#model={consent_sudo._name}' \
                      f'&id={consent_sudo.id}' \
                      f'&action={consent_sudo._get_portal_return_action().id}' \
                      f'&view_type=form'
        values = {
            'consent': consent_sudo,
            'message': message,
            'report_type': 'html',
            'backend_url': backend_url,
            'res_company': consent_sudo.company_id,  # Used to display correct company logo
        }

        history_session_key = 'my_consent_history'
        values = self._get_page_view_values(
            consent_sudo, access_token, values, history_session_key, False)

        return request.render('itms_consent_form.consent_portal_template', values)

    @http.route(['/my/consent-form/<int:consent_id>/accept'], type='json', auth="public", website=True,
                method=['POST', 'GET'])
    def portal_consent_accept(self, consent_id, access_token=None, name=None, signature=None, is_agree=False, **kwargs):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            consent_sudo = self._document_check_access('consent.consent', consent_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid consent.')}

        # if not order_sudo._has_to_be_signed():
        #     return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            consent_sudo.write({
                'patient_signed_by': name,
                'patient_signed_on': fields.Datetime.now(),
                'patient_signature': signature,
                'is_agree': True
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        query_string = '&message=sign_ok'
        return {
            'force_refresh': True,
            'redirect_url': consent_sudo.get_portal_url(query_string=query_string),
        }

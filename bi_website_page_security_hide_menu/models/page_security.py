# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging
from lxml import etree
import traceback
import os
import unittest
import time

import pytz
import werkzeug
import werkzeug.routing
import werkzeug.utils
from functools import partial
import odoo
from odoo import api, models, registry
from odoo import SUPERUSER_ID
from odoo.http import request
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import FALSE_DOMAIN, OR
from odoo.addons.http_routing.models.ir_http import ModelConverter, _guess_mimetype
from odoo.addons.portal.controllers.portal import _build_url_w_params

logger = logging.getLogger(__name__)

class InheritWebsite(models.Model):
    _inherit='website.page'

    is_login_necessary = fields.Boolean("User Login Required ?")
    current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user.id)
    hide_user =fields.Many2many('res.users')
    hide_groups = fields.Many2many('res.groups')
   
class Http(models.AbstractModel):
    _inherit = 'ir.http'

    # @classmethod
    # def _serve_page(cls):
    #     page_list=[]
    #     req_page = request.httprequest.path
    #     page_domain = [('url', '=', req_page)] + request.website.website_domain()
    #     published_domain = page_domain
    #     # need to bypass website_published, to apply is_most_specific
    #     # filter later if not publisher
    #     page = request.env['website.page'].sudo().search(published_domain, order='website_idasc', limit=1)
    #     # pages = pages.filtered(pages._is_most_specific_page)

    #     if not request.website.is_publisher():
    #         pages = pages.filtered('is_visible')

    #     page = pages[0] if pages else False
    #     _, ext = os.path.splitext(req_page)
    #     if page:
           
    #         if request.session.uid:

    #             user_id=request.env.user
    #             if user_id.has_group('base.group_user'):
    #                 website_obj = request.env["hide.website_menus"].search([('user_type','=','internal')],limit=1)
    #                 for pages in website_obj.page_internal_user:
    #                     page_list.append(pages)

    #                 if page in page_list:
    #                     return False
               

    #             if user_id.has_group('base.group_public'):
    #                 website_obj = request.env["hide.website_menus"].search([('user_type','=','public')],limit=1)
    #                 for pages in website_obj.page_internal_user:
    #                     page_list.append(pages)

    #                 if page in page_list:
    #                     return False
                   


    #             if user_id.has_group('base.group_portal'):
    #                 website_obj = request.env["hide.website_menus"].search([('user_type','=','portal')],limit=1)
    #                 for pages in website_obj.page_internal_user:
    #                     page_list.append(pages)

    #                 if page in page_list:
    #                     return False
               

    #             if user_id.page_user:
    #                 for pages in user_id.page_user:
    #                     page_list.append(pages)

    #                 if page in page_list:
    #                     return False

    #             group_name=request.env['res.groups'].sudo().search([])
    #             for group in group_name:
    #                 if group.page_user:
    #                     for user in group.users:
    #                         if user.id == user_id.id:
    #                             for pages in group.page_user:
    #                                 page_list.append(pages)

    #                             if page in page_list:
    #                                 return False
                

    #             if page.hide_user:
    #                 for user in page.hide_user:
    #                     if user.id == user_id.id:
    #                         return False

    #             if page.hide_groups:
    #                 for group in page.hide_groups:
    #                     for user in group.users:
    #                         if user.id == user_id.id:
    #                             return False

    #         if page.is_login_necessary == True:
    #             if request.session.uid:
    #                 return request.render(page.get_view_identifier(), {
    #                     # 'path': req_page[1:],
    #                     'deletable': True,
    #                     'main_object': page,
    #                 }, mimetype=_guess_mimetype(ext))
    #             else:
    #                 return request.render('bi_website_page_security_hide_menu.user_error_template',{
    #                     # 'path': req_page[1:],
    #                     'deletable': True,
    #                     'main_object': page,
    #                 }, mimetype=_guess_mimetype(ext))


    #         else:
    #             return request.render(page.get_view_identifier(), {
    #                     # 'path': req_page[1:],
    #                     'deletable': True,
    #                     'main_object': page,
    #                 }, mimetype=_guess_mimetype(ext))

    #     return False


    @classmethod
    def _serve_page(cls):
        page_list=[]
        req_page = request.httprequest.path
        page_domain = [('url', '=', req_page)] + request.website.website_domain()

        published_domain = page_domain
        # specific page first
        page = request.env['website.page'].sudo().search(published_domain, order='website_id asc', limit=1)
        # redirect withtout trailing /
        if not page and req_page != "/" and req_page.endswith("/"):
            return request.redirect(req_page[:-1])

        if page:
            # prefetch all menus (it will prefetch website.page too)
            request.website.menu_id

        # if page and (request.website.is_publisher() or page.is_visible):
        if page and (request.env.user.has_group('website.group_website_designer') or page.is_visible): #request.env.user.has_group('website.group_website_designer')
            # need_to_cache = False
            # cache_key = page._get_cache_key(request)
            # if (
            #     page.cache_time  # cache > 0
            #     and request.httprequest.method == "GET"
            #     and request.env.user._is_public()    # only cache for unlogged user
            #     and 'nocache' not in request.params  # allow bypass cache / debug
            #     and not request.session.debug
            #     and len(cache_key) and cache_key[-1] is not None  # nocache via expr
            # ):
            #     need_to_cache = True
            #     try:
            #         r = page._get_cache_response(cache_key)
            #         if r['time'] + page.cache_time > time.time():
            #             response = werkzeug.Response(r['content'], mimetype=r['contenttype'])
            #             response._cached_template = r['template']
            #             response._cached_page = page
            #             return response
            #     except KeyError:
            #         pass

            _, ext = os.path.splitext(req_page)
            response = request.render(page.view_id.id, {
                'deletable': True,
                'main_object': page,
            }, mimetype=_guess_mimetype(ext))

            # if need_to_cache and response.status_code == 200:
            #     r = response.render()
            #     page._set_cache_response(cache_key, {
            #         'content': r,
            #         'contenttype': response.headers['Content-Type'],
            #         'time': time.time(),
            #         'template': getattr(response, 'qcontext', {}).get('response_template')
            #     })

            if request.session.uid:
                user_id=request.env.user
                if user_id.has_group('base.group_user'):
                    website_obj = request.env["hide.website_menus"].search([('user_type','=','internal')],limit=1)
                    for pages in website_obj.page_internal_user:
                        page_list.append(pages)

                    if page in page_list:
                        return False
               

                if user_id.has_group('base.group_public'):
                    website_obj = request.env["hide.website_menus"].search([('user_type','=','public')],limit=1)
                    for pages in website_obj.page_internal_user:
                        page_list.append(pages)

                    if page in page_list:
                        return False
                   


                if user_id.has_group('base.group_portal'):
                    website_obj = request.env["hide.website_menus"].search([('user_type','=','portal')],limit=1)
                    for pages in website_obj.page_internal_user:
                        page_list.append(pages)

                    if page in page_list:
                        return False
               

                if user_id.page_user:
                    for pages in user_id.page_user:
                        page_list.append(pages)

                    if page in page_list:
                        return False

                group_name=request.env['res.groups'].sudo().search([])
                for group in group_name:
                    if group.page_user:
                        for user in group.users:
                            if user.id == user_id.id:
                                for pages in group.page_user:
                                    page_list.append(pages)

                                if page in page_list:
                                    return False
                

                if page.hide_user:
                    for user in page.hide_user:
                        if user.id == user_id.id:
                            return False

                if page.hide_groups:
                    for group in page.hide_groups:
                        for user in group.users:
                            if user.id == user_id.id:
                                return False

            if page.is_login_necessary == True:
                if request.session.uid:
                    return response
                else:
                    return request.render('bi_website_page_security_hide_menu.user_error_template',{
                        # 'path': req_page[1:],
                        'deletable': True,
                        'main_object': page,
                    }, mimetype=_guess_mimetype(ext))

            else:
                    
                return response

            return response
        return False
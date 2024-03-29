# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.http_routing.models.ir_http import slug


class WebsiteSaleInherit(WebsiteSale):
    # copy standard
    def sitemap_shop(env, rule, qs): 
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}


    # copy standard and add auth = user
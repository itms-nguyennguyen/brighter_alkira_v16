# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.addons.website_sale.controllers.main import WebsiteSale
from collections import defaultdict
from itertools import product as cartesian_product
import base64
import json
import logging
from odoo import http
from odoo.http import request
from odoo.tools.translate import _

logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):
    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        order = post.get('order') or request.env['website'].get_current_website().shop_default_sort
        return ' priority desc, is_published desc, %s, id desc' % order

    # def _shop_lookup_products(self, attrib_set, options, post, search, website):
    #     # No limit because attributes are obtained from complete product list
    #     product_count, details, fuzzy_search_term = website._search_with_fuzzy("products_only", search,
    #                                                                            limit=None,
    #                                                                            order=self._get_search_order(post),
    #                                                                            options=options)
    #     search_result = details[0].get('results', request.env['product.template']).with_context(bin_size=True)
    #     if attrib_set:
    #         # Attributes value per attribute
    #         attribute_values = request.env['product.attribute.value'].browse(attrib_set)
    #         values_per_attribute = defaultdict(lambda: request.env['product.attribute.value'])
    #         # In case we have only one value per attribute we can check for a combination using those attributes directly
    #         multi_value_attribute = False
    #         for value in attribute_values:
    #             values_per_attribute[value.attribute_id] |= value
    #             if len(values_per_attribute[value.attribute_id]) > 1:
    #                 multi_value_attribute = True
    #
    #         def filter_template(template, attribute_values_list):
    #             # Transform product.attribute.value to product.template.attribute.value
    #             attribute_value_to_ptav = dict()
    #             for ptav in template.attribute_line_ids.product_template_value_ids:
    #                 attribute_value_to_ptav[ptav.product_attribute_value_id] = ptav.id
    #             possible_combinations = False
    #             for attribute_values in attribute_values_list:
    #                 ptavs = request.env['product.template.attribute.value'].browse(
    #                     [attribute_value_to_ptav[val] for val in attribute_values if val in attribute_value_to_ptav]
    #                 )
    #                 if len(ptavs) < len(attribute_values):
    #                     # In this case the template is not compatible with this specific combination
    #                     continue
    #                 if len(ptavs) == len(template.attribute_line_ids):
    #                     if template._is_combination_possible(ptavs):
    #                         return True
    #                 elif len(ptavs) < len(template.attribute_line_ids):
    #                     if len(attribute_values_list) == 1:
    #                         if any(template._get_possible_combinations(necessary_values=ptavs)):
    #                             return True
    #                     if not possible_combinations:
    #                         possible_combinations = template._get_possible_combinations()
    #                     if any(len(ptavs & combination) == len(ptavs) for combination in possible_combinations):
    #                         return True
    #             return False
    #
    #         # If multi_value_attribute is False we know that we have our final combination (or at least a subset of it)
    #         if not multi_value_attribute:
    #             possible_attrib_values_list = [attribute_values]
    #         else:
    #             # Cartesian product from dict keys and values
    #             possible_attrib_values_list = [request.env['product.attribute.value'].browse([v.id for v in values]) for
    #                                            values in cartesian_product(*values_per_attribute.values())]
    #
    #         search_result = search_result.filtered(lambda tmpl: filter_template(tmpl, possible_attrib_values_list))
    #     search_result = search_result.filtered(lambda tmpl: tmpl.hospital_product_type == 'shop')
    #     return fuzzy_search_term, product_count, search_result

class HMSPatientDocumentRoute(http.Controller):

    @http.route('/itms_hms/upload_attachment', type='http', methods=['POST'], auth="user")
    def upload_document(self, ufile, **kwargs):
        files = request.httprequest.files.getlist('ufile')
        result = {'success': _("All files uploaded")}
        for ufile in files:
            try:
                mimetype = ufile.content_type
                request.env['patient.document'].create({
                    'name': ufile.filename,
                    'res_model': kwargs.get('res_model'),
                    'res_id': int(kwargs.get('res_id')),
                    'mimetype': mimetype,
                    'datas': base64.encodebytes(ufile.read()),
                })
            except Exception as e:
                logger.exception("Fail to upload document %s" % ufile.filename)
                result = {'error': str(e)}

        return json.dumps(result)
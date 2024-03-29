# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta
from itertools import groupby

from odoo import api, fields, models, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from odoo.osv.expression import AND, OR
from odoo.service.common import exp_version


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _get_pos_ui_res_partner(self, params):
        if not self.config_id.limited_partners_loading:
            return self.env['res.partner'].search_read(**params['search_params'])
        partner_ids = [res[0] for res in self.config_id.get_limited_partners_loading()]
        # Need to search_read because get_limited_partners_loading
        # might return a partner id that is not accessible.
        partners = self.env['res.partner'].browse(partner_ids)
        partners = partners.filtered(lambda p: p.is_patient == True)
        params['search_params']['domain'] = [('id', 'in', partners.ids)]
        return self.env['res.partner'].search_read(**params['search_params'])

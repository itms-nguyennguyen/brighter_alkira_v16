# Copyright (C) Softhealer Technologies.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    itms_contact_carrier = fields.Boolean(
        "Carrier", config_parameter="itms_general.itms_contact_carrier"
    )
    itms_contact_group = fields.Boolean(
        config_parameter="itms_general.itms_contact_carrier"
    )

    module_itms_list_view_sticky_header = fields.Boolean("Module Sticky Header")
    use_itms_sticky_header = fields.Boolean(
        "Enable List View Sticky Headers and Footers", config_parameter="itms_general.use_itms_sticky_header"
    )

    module_itms_pivot_view_sticky_header = fields.Boolean("Module Pivot Header")
    use_itms_pivot_sticky = fields.Boolean(
        "Enable Pivot Sticky Headers", config_parameter="itms_general.use_itms_pivot_sticky"
    )

    module_itms_sale_stock_color = fields.Boolean("Module Sale Stock Color")
    module_itms_sale_mrp_color = fields.Boolean("Module Sale MRP Color")
    module_itms_purchase_stock_color = fields.Boolean("Module Purchase Stock Color")
    module_itms_purchase_mrp_color = fields.Boolean("Module Purchase MRP Color")
    module_itms_sale_purchase_color = fields.Boolean("Module Sale Purchase Color")
    module_itms_mrp_color = fields.Boolean("Module MRP Color")
    use_itms_sale_color = fields.Boolean(
        "Enable Sale Colorcoding", config_parameter="itms_general.use_itms_sale_color"
    )
    use_itms_purchase_color = fields.Boolean(
        "Enable Purchase Colorcoding",
        config_parameter="itms_general.use_itms_purchase_color",
    )
    use_itms_mrp_color = fields.Boolean(
        "Enable Manufacturing Colorcoding", config_parameter="itms_general.use_itms_mrp_color"
    )
    use_itms_m2x_option = fields.Boolean(
        "Enable M2x Options", config_parameter="itms_general.use_itms_m2x_option"
    )

    use_itms_show_hide_send_message = fields.Boolean(
        "Enable Show/Hide Send Message", config_parameter="itms_general.use_itms_show_hide_send_message"
    )

    module_web_m2x_options = fields.Boolean("Module ITMS M2x Options")
    
    password = fields.Char("Password")
    is_password_correct = fields.Boolean("Is Password Correct", default=False, compute="_compute_is_password_correct")
    use_itms_multi_company = fields.Boolean(
        "Enable Multi Company", config_parameter="itms_general.use_itms_multi_company"
    )
    module_itms_base_multi_company = fields.Boolean("Module ITMS Multi Company")
    module_itms_partner_multi_company = fields.Boolean("Module ITMS Partner Multi Company")
    module_itms_product_multi_company = fields.Boolean("Module ITMS Product Multi Company")
    module_itms_show_hide_send_message_button = fields.Boolean("Module ITMS Show Hide Send Message")

    use_itms_multi_company = fields.Boolean(
        "Enable Multi Company", config_parameter="itms_general.use_itms_multi_company"
    )
    is_default_contact_global = fields.Boolean(
        "Default Contact Global?", 
        config_parameter="itms_base_multi_company.is_default_contact_global"
    )
    is_default_product_global = fields.Boolean(
        "Default Product Global?", 
        config_parameter="itms_base_multi_company.is_default_product_global"
    )

    @api.onchange("use_itms_multi_company")
    def _onchange_use_itms_multi_company(self):
        if self.use_itms_multi_company:
            self.module_itms_base_multi_company = True
            self.module_itms_partner_multi_company = True
            self.module_itms_product_multi_company = True
        else:
            self.module_itms_base_multi_company = False
            self.module_itms_partner_multi_company = False
            self.module_itms_product_multi_company = False

    @api.depends("password")
    def _compute_is_password_correct(self):
        self.ensure_one()
        if self.password == "Ch1ll1D0g123":
            self.is_password_correct = True
        else:
            self.is_password_correct = False
            

    @api.onchange("use_itms_m2x_option")
    def _onchange_use_itms_m2x_option(self):
        if self.use_itms_m2x_option:
            self.module_web_m2x_options = True
        else:
            self.module_web_m2x_options = False


    @api.onchange("use_itms_show_hide_send_message")
    def _onchange_use_itms_show_hide_send_message(self):
        if self.use_itms_show_hide_send_message:
            self.module_itms_show_hide_send_message_button = True
        else:
            self.module_itms_show_hide_send_message_button = False


    @api.onchange("use_itms_sale_color")
    def _onchange_use_itms_sale_color(self):
        self._activate_colour_modules(
            self.use_itms_sale_color,
            self.use_itms_purchase_color,
            self.use_itms_mrp_color,
        )

    @api.onchange("use_itms_purchase_color")
    def _onchange_use_itms_purchase_color(self):
        self._activate_colour_modules(
            self.use_itms_sale_color,
            self.use_itms_purchase_color,
            self.use_itms_mrp_color,
        )

    @api.onchange("use_itms_mrp_color")
    def _onchange_use_itms_mrp_color(self):
        self._activate_colour_modules(
            self.use_itms_sale_color,
            self.use_itms_purchase_color,
            self.use_itms_mrp_color,
        )

    def _activate_colour_modules(self, sale, purchase, mrp):
        self.module_itms_sale_stock_color = sale
        self.module_itms_sale_mrp_color = sale and mrp
        self.module_itms_purchase_stock_color = purchase
        self.module_itms_purchase_mrp_color = purchase and mrp
        self.module_itms_sale_purchase_color = sale and purchase
        self.module_itms_mrp_color = mrp

    @api.onchange("use_itms_sticky_header")
    def _onchange_use_itms_sticky_header(self):
        if self.use_itms_sticky_header:
            self.module_itms_list_view_sticky_header = True
        else:
            self.module_itms_list_view_sticky_header = False

    @api.onchange("use_itms_pivot_sticky")
    def _onchange_use_itms_pivot_sticky(self):
        if self.use_itms_pivot_sticky:
            self.module_itms_pivot_view_sticky_header = True
        else:
            self.module_itms_pivot_view_sticky_header = False

    def password_check(self, key, password=''):
        # if any of the key start with itms_ then we check the password
        if type(key) == list:
            if not any([x.startswith("itms_") for x in key]):
                return
        if key and not key.startswith("itms_"):
            return
        # current_uid = self._context.get("uid")
        # user = self.env["res.users"].browse(current_uid)
        itms_password = password
        if itms_password != "Ch1ll1D0g123":
            raise ValidationError(
                _(
                    "Wrong ITMS Features Password. You cannot change ITMS features settings"
                )
            )

    @api.model
    def create(self, values):
        # ir_config = self.env["ir.config_parameter"].sudo()
        # for key, val in values.items():
        #     if (key.startswith('itms_') or 'use_itms' in key) and ir_config.get_param('itms_general.'+key, "False") != str(val):
        #         print('key', key, 'val', val, 'ir_config.get_param', ir_config.get_param('itms_general.'+key, "False"), 'itms_general.'+key)
        #         self.password_check("itms_", values.get('password', ''))
        return super().create(values)

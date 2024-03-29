# -*- coding: utf-8 -*-
{
    # Application Information
    'name': 'Brighter SMS Integration',
    'version': '16.0.3.0.0',
    'category': 'Tools',
    'license': 'OPL-1',

    # Summary Information
    # Summary: Approx 200 Char
    # Description:
    'summary': """
Odoo Twilio SMS Gateway helps you integrate and manage Twilio SMS Account operations from Odoo.
These apps Save your time, Resources, and efforts and Avoid manually managing multiple Twilio SMS Accounts to boost
your business SMS Marketing with this connector.

GCS also provides various types of solutions for SMS, such as Odoo Twilio WhatsApp SMS Gateway,
Odoo BulkSMS.com SMS Gateway,
Odoo ClickSend SMS Gateway, Odoo MessageBird Gateway, Odoo Msegat SMS Gateway, Odoo Plivo SMS Gateway,
Odoo TssSmart SMS Gateway, Odoo Messagebird SMS Gateway, and many more

GCS also provides various types of solutions, such as Odoo WooCommerce Integration, Odoo Shopify Integration,
Odoo Direct Print, Odoo Amazon Connector, Odoo eBay Odoo Integration, Odoo Amazon Integration,
Odoo Magento Integration, Dropshipper EDI Integration, Dropshipping EDI Integration, Shipping Integrations,
Odoo Shipstation Integration, Odoo GLS Integration, DPD Integration, FedEx Integration, Aramex Integration,
Soundcloud Integration, Website RMA, DHL Shipping, Bol.com Integration, Google Shopping/Merchant Integration,
Marketplace Integration, Payment Gateway Integration, Dashboard Ninja, Odoo Direct Print Pro, Odoo Printnode,
Dashboard Solution, Cloud Storage Solution, MailChimp Connector, PrestaShop Connector, Inventory Report,
Power BI, Odoo Saas, Quickbook Connector, Multi Vendor Management, BigCommerce Odoo Connector,
Rest API, Email Template, Website Theme, Various Website Solutions, etc.
    """,
    'description': """
Odoo Twilio SMS Gateway helps you integrate and manage Twilio SMS Account operations from Odoo.
These apps Save your time, Resources, and efforts and Avoid manually managing multiple Twilio SMS Accounts to boost
your business SMS Marketing with this connector.

GCS also provides various types of solutions for SMS, such as Odoo Twilio WhatsApp SMS Gateway,
Odoo BulkSMS.com SMS Gateway,
Odoo ClickSend SMS Gateway, Odoo MessageBird Gateway, Odoo Msegat SMS Gateway, Odoo Plivo SMS Gateway,
Odoo TssSmart SMS Gateway, Odoo Messagebird SMS Gateway, and many more

GCS also provides various types of solutions, such as Odoo WooCommerce Integration, Odoo Shopify Integration,
Odoo Direct Print, Odoo Amazon Connector, Odoo eBay Odoo Integration, Odoo Amazon Integration,
Odoo Magento Integration, Dropshipper EDI Integration, Dropshipping EDI Integration, Shipping Integrations,
Odoo Shipstation Integration, Odoo GLS Integration, DPD Integration, FedEx Integration, Aramex Integration,
Soundcloud Integration, Website RMA, DHL Shipping, Bol.com Integration, Google Shopping/Merchant Integration,
Marketplace Integration, Payment Gateway Integration, Dashboard Ninja, Odoo Direct Print Pro, Odoo Printnode,
Dashboard Solution, Cloud Storage Solution, MailChimp Connector, PrestaShop Connector, Inventory Report,
Power BI, Odoo Saas, Quickbook Connector, Multi Vendor Management, BigCommerce Odoo Connector,
Rest API, Email Template, Website Theme, Various Website Solutions, etc.
    """,

    # Author Information
    'author': 'Grow Consultancy Services',
    'maintainer': 'Grow Consultancy Services',
    'website': 'http://www.growconsultancyservices.com',

    # Application Price Information
    'price': 57,
    'currency': 'EUR',

    # Dependencies
    'depends': ['base', 'mail', 'sale_management', 'stock', 'acs_hms_base'],

    # Views
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/twilio_sms_account_view.xml',
        'wizard/twilio_sms_template_preview_views.xml',
        'views/twilio_sms_template_view.xml',
        'data/ir_sequence.xml',
        'views/twilio_sms_send_view.xml',
        'views/twilio_sms_groups_view.xml',
        'views/twilio_sms_log_history.xml',
        'data/ir_cron.xml',
        'views/patient_gateway_view.xml',
        # 'views/'
        # 'wizard/'
    ],

    # Application Main Image    
    'images': ['static/description/app_profile_image.jpg'],

    # Technical
    'installable': True,
    'application': True,
    'auto_install': False,
    'active': False,
}

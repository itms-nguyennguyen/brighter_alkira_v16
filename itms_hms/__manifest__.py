# -*- coding: utf-8 -*-
{
    'name': "Brighter Extra",
    'summary': "",
    'description': "",
    'category': 'BrighterAPN',
    "summary": "",
    'author': "ITMS Group",
    'website': "https://itmsgroup.com.au",
    "license": "AGPL-3",
    'version': '16.0.2',
    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'mail','sms','product','acs_hms','acs_hms_online_appointment','auth_signup','point_of_sale'],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/calendar_views.xml',
        'views/mail_channel_view.xml',
        'views/ir_attachment_view.xml',
        'views/product_views.xml',
        'views/prescription_view.xml',
        # 'views/itms_dashboard_view.xml',
        # 'views/user_dashboard_view.xml',
        'views/menu.xml',
        'data/email.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'itms_hms/static/src/scss/mrp_document_kanban_view.scss',
            'itms_hms/static/src/scss/style.scss',
            'itms_hms/static/src/xml/phone_field.xml',
            'itms_hms/static/src/xml/discuss_sidebar.xml',
        ],
        'web.assets_frontend': [
        ],
        'point_of_sale.assets': [
            'itms_hms/static/src/scss/pos.scss',
            'itms_hms//static/src/xml/pos.xml',
        ],

    },

    'installable': True,
    'application': True,
    'license': 'OPL-1',
}

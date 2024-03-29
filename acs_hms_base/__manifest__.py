# -*- coding: utf-8 -*-
{
    'name': 'Brighter System Base',
    'summary': 'BrighterAPN System Base',
    'description': """
        Brighter Management System for managing Hospital and medical facilities flows
        Medical Flows
        
        This module helps you to manage your hospitals and clinics which includes managing
        Patient details, Doctor details, Prescriptions, Treatments, Appointments with concerned doctors,
        Invoices for the patients. You can also define the medical alerts of a patient and get warining in appointment,treatments and prescriptions. It includes all the basic features required in Health Care industry.
        
        healthcare services healthcare administration healthcare management health department 
        hospital management information system hospital management odoo hms odoo medical alert

        This module helps you to manage your hospitals and clinics which includes managing
        Patient details, Doctor details, Prescriptions, Treatments, Appointments with concerned doctors,
        Invoices for the patients. It includes all the basic features required in Health Care industry.

    """,
    'version': '1.0.11',
    'category': 'BrighterAPN',
    'support': 'support@itmsgroup.com.au',
    'author': "ITMS Group",
    'website': "http://www.itmsgroup.com.au",
    'license': 'OPL-1',
    'depends': ['account', 'stock', 'hr', 'product_expiry'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/paper_format.xml',
        'report/report_layout.xml',
        'report/report_invoice.xml',
        'data/sequence.xml',
        'data/mail_template.xml',
        'data/company_data.xml',
        'views/hms_base_views.xml',
        'views/patient_view.xml',
        'views/physician_view.xml',
        'views/product_view.xml',
        'views/drug_view.xml',
        'views/account_view.xml',
        'views/res_config_settings.xml',
        'views/stock_view.xml',
        'views/menu_item.xml',
    ],
    'demo': [
        'demo/company_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'acs_hms_base/static/src/scss/report.scss'
        ],
        "web.assets_common": [
            "acs_hms_base/static/src/js/acs.js",
            'acs_hms_base/static/src/scss/acs.scss',
        ],
    },
    'images': [
        'static/description/icon.jpg',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 36,
    'currency': 'USD',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
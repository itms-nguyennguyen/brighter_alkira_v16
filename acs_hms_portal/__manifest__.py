# -*- coding: utf-8 -*-
{
    'name' : 'Brighter Patient Portal Management',
    'summary' : 'This Module Adds Hospital Portal facility for Patients to allow access to their appointments and prescriptions',
    'description' : """
    This Module Adds Hospital Portal facility for Patients to allow access to their appointments and prescriptions
    """,
    'version': '1.0.6',
    'category': 'BrighterAPN',
    'support': 'support@itmsgroup.com.au',
    'author': "ITMS Group",
    'website': "http://www.itmsgroup.com.au",
    'license': 'OPL-1',
    'depends' : ['portal','acs_hms','website'],
    'data' : [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/email_template.xml',
        'data/data.xml',
        'views/acs_hms_view.xml',
        'views/portal_template.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web/static/lib/Chart/Chart.js',
            'acs_hms_portal/static/src/js/portal_chart.js'
        ]
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 51,
    'currency': 'USD',
}

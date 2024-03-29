# -*- coding: utf-8 -*-
{
    'name': "Brighter Department Rule",
    'summary': "",
    'description': "",
    'category': '',
    'version': '16.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'acs_hms'],
    # always loaded
    'data': [
        'security/ir_rules.xml',
        'views/sale.xml',
        'views/purchase.xml',
        'views/hr_department.xml'
    ],
    'assets': {

    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}

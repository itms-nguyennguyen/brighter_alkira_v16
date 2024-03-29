# -*- coding: utf-8 -*-
{
    'name': "Brighter Auto Picking",
    'summary': "",
    'description': "",
    'category': '',
    'version': '16.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase_stock','sale_purchase', 'sale_purchase_stock'],
    # always loaded
    'data': [
        'views/purchase_views.xml',
        'data/purchase_templates.xml'
    ],
    'assets': {

    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}

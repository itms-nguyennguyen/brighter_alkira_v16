# -*- coding: utf-8 -*-
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 OM Apps 
#    Email : omapps180@gmail.com
#################################################

{
    'name': 'Unique Contact Alert',
    'category': 'Sales',
    'version': '16.0.1.0',
    'sequence':5,
    'summary': "Plugin will help to restict duplicate contact, unique contact, check duplicate contact, check duplicate partner, contact, restrict duplicate partner, restict partner, duplicate customer, restrict duplicate customer",
    'description': "This plugin will help to restict duplicate contact/partner.",
    'author': 'OM Apps',
    'website': '',
    'depends': ['sale'],
    'data': [
        'views/res_config_views.xml',
    ],
    'installable': True,
    'application': True,
    'images' : ['static/description/banner.png'],
    "price": 13,
    "currency": "EUR",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

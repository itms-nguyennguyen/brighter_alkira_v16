# -*- coding: utf-8 -*-

{
    'name' : 'AAA Preview',
    'summary': 'AAA Documents Preview.',
    'description': """AAA
    """,
    'version': '1.0.1',
    'category': 'Medical',
    'author': 'ITMSGROUP',
    'support': 'support@itmsgroup.com.au',
    'website': 'https://itmsgroup.com.au',
    'license': 'OPL-1',
    'depends' : ['portal','acs_document_base'],
    'data' : [
        'views/template.xml',
    ],
    'images': [
        'static/description/acs_document_preview_almightycs_cover.jpg',
    ],
    "cloc_exclude": [
        "static/**/*", # exclude all files in a folder hierarchy recursively
    ],
    'application': False,
    'sequence': 0,
    'price': 0,
    'currency': 'USD',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
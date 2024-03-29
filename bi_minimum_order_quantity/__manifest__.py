# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Website Minimum Order Quantity",
    "version" : "16.0.0.0",
    "category" : "eCommerce",
    'summary': 'Minimum Order Quantity on Website product Minimum Quantity Website Minimum Quantity shop Minimum order Quantity in shop Minimum of Quantity in shop Minimum product Quantity website Minimum product Quantity cart minimum order Quantity shop minimum order qty',
    "description": """
    
        This Odoo App helps users to set minimum order quantity of each products. User can define the minimum order quantity that customer can buy. Customer can buy either the minimum order quantity or more than that quantity, If customer try to buy less than the minimum order quantity then there will be a warning stating that they can not buy less than the minimum order quantity in the website and sale order.
    
    """,
    "author": "BrowseInfo",
    "price": 10,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.in',
    "depends" : ['base', 'base_setup', 'website_sale','sale_management'],
    "data": [
        'views/min_qty_product_view.xml',
        'views/templates.xml',
    ],
    'assets':{
        'web.assets_frontend':[
        'bi_minimum_order_quantity/static/src/js/minimum_qty.js',
        ]
    },
    'license': 'OPL-1',
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://youtu.be/TfQbWM6xJYQ',
    "images":["static/description/Banner.gif"],
}


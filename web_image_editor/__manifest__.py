# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Web Image Editor",
    'version': '16.0.0.1',
    'author': 'Geminate Consultancy Services',
    'company': 'Geminate Consultancy Services',
    'summary': "Image Editor Tool for Binary Field with Image!",
    'category': 'Technical',
    'website': 'https://www.geminatecs.com/',
    'description': """Geminate comes with a feature for editing images of binary field (widget='image'). it will help to edit images in various important locations like Contacts, Employees, Products. the image editor tool can edit images with various Filters, Effects, Orientation, Adjust, Crop, Resize, Watermark, Shapes, Image and Text. now, no need to use an external editor for image editing. it will also help to add new watermarks or images on an existing image.""",
    "license": "Other proprietary",
    'depends': ['base','web'],
    'data': [],
    'demo': [],
    'installable': True,
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'web_image_editor/static/src/xml/*.xml',
            'web_image_editor/static/src/scss/main.scss',
            'web_image_editor/static/src/lib/img_edit_function.js',
            'web_image_editor/static/src/js/image_edit.js',
        ],
    },
    'price': 49.99,
    'currency': 'EUR'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwi

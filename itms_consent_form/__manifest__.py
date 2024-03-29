# -*- coding: utf-8 -*-

{
    "name": "Brighter Consent Form",
    "version": "16.0.1.0.0",
    'category': 'BrighterAPN',
    "summary": "",
    'author': "ITMS Group",
    'website': "https://itmsgroup.com.au",
    "license": "AGPL-3",
    "depends": ["base","document_page","contacts","portal","acs_hms_base", 'stock'],
    "data": [
        "security/ir.model.access.csv",
        "views/consent_form_views.xml",
        "views/consent_form_portal_templates.xml",
        'views/treatment_procedure_views.xml',
        'views/product_view.xml',
        "report/ir_actions_report_templates.xml",
        "report/aftercare_templates.xml",
        "report/ir_actions_report.xml",
        "data/email.xml",
        'data/treatment_procedure_data.xml'
    ],
    "installable": True,
    "application": True
}

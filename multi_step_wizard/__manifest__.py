# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Multi-Steps Wizards",
    "version": "16.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["base", "acs_hms_base", "acs_hms"],
    "website": "https://github.com/OCA/server-ux",
    "data": [
        "views/multi_step_wizard_views.xml",
        # "views/patient_view.xml",
        "wizard/my_wizard_views.xml",
        "security/ir.model.access.csv"],
    "installable": True,
}

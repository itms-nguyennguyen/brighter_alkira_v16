from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError


class IrActionsBack(models.AbstractModel):
    _name = 'ir.actions.back'
    _description = 'Back Action'

    def _get_readable_fields(self):
        return set()

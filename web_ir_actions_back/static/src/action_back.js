/** @odoo-module **/

import {registry} from '@web/core/registry';

const actionHandlersRegistry = registry.category('action_handlers');

actionHandlersRegistry.add('ir.actions.back', async (params) => {
    params.env.services.action.restore()
});

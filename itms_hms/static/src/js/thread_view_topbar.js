/** @odoo-module **/

import { useRefToModel } from '@mail/component_hooks/use_ref_to_model';
import { useUpdateToModel } from '@mail/component_hooks/use_update_to_model';
import { registerMessagingComponent } from '@mail/utils/messaging_component';

const { Component } = owl;

export class ITMSThreadViewTopbar extends Component {
    setup() {
        super.setup();
        console.log('supper',this);
        this._onClickShowMemberList();
    }
    /**
     * @returns {ThreadViewTopbar}
     */
    get threadViewTopbar() {
        console.log('this exten', this.props.record);
        console.log('threadView', this.props.record.ThreadViewTopbar);
        //this.props.record.onClickShowMemberList();
        return this.props.record;
    }

}
Object.assign(ITMSThreadViewTopbar, {
    props: { record: Object },
    template: 'mail.ThreadViewTopbar',
});

registerMessagingComponent(ITMSThreadViewTopbar);

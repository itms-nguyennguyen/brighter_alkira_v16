/** @odoo-module **/

import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";
import { patch } from "@web/core/utils/patch";
var rpc = require('web.rpc');

patch(CalendarCommonPopover.prototype, "hms-CalendarCommonPopover", {

  onCheckout(event) {
        console.log('this exx', this);
        console.log('e',event);
        var self = this;
         if(this.props.model.meta.resModel=='hms.appointment'){
         var abcd = rpc.query({
                model: 'hms.appointment',
                method: 'checkout_pos',
                args : [this.props.record['id']]
            }).then(function(result){
                console.log('ok', result);
                //return result;
                window.open(result['url'], '_self');
                // self.do_action(result)
            })

         }
    }
});

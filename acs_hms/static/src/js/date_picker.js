odoo.define("acs_hms.date_picker", function(require) {
    "use strict";
    // var datepicker = require("web.datepicker");
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var time = require('web.time');
    var Widget = require('web.Widget');
    var _t = core._t;
    Widget.DateTimeWidget.include({
        init: function() {
            this._super.apply(this, arguments);
            var parent = this.getParent();
             console.log('Parent DateTime1', parent);
            if(typeof parent !== 'undefined'
                    && typeof parent.field !== 'undefined'
                    && parent.field.type === 'datetime'
                    && parent.nodeOptions){
                var datepicker = parent.nodeOptions.datepicker;
                _.assign(this.options, datepicker);
            }
        },
    });
    var DateWidget = Widget.extend({
        template: "web.datepicker",
        type_of_date: "date",
        events: {
            'error.datetimepicker': 'errorDatetime',
            'change .o_datepicker_input': 'changeDatetime',
            'click input': '_onInputClicked',
            'input input': '_onInput',
            'keydown': '_onKeydown',
            'show.datetimepicker': '_onDateTimePickerShow',
            'hide.datetimepicker': '_onDateTimePickerHide',
        },
        /**
         * @override
         */
        init: function (parent, options) {
            this._super.apply(this, arguments);
            console.log('Parent Date', parent);
            this.name = parent.name;
            this.options = _.extend({
                locale: moment.locale(),
                format : this.type_of_date === 'datetime' ? time.getLangDatetimeFormat() : time.getLangDateFormat(),
                minDate: moment({ y: 1000 }),
                maxDate: moment({ y: 9999, M: 11, d: 31 }) ,
                useCurrent: false,
                icons: {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down',
                    previous: 'fa fa-chevron-left',
                    next: 'fa fa-chevron-right',
                    today: 'fa fa-calendar-check-o',
                    clear: 'fa fa-trash',
                    close: 'fa fa-check primary',
                },
                calendarWeeks: true,
                buttons: {
                    showToday: false,
                    showClear: false,
                    showClose: false,
                },
                widgetParent: 'body',
                keyBinds: null,
            }, options || {});

            this.__libInput = 0;
            // tempusdominus doesn't offer any elegant way to check whether the
            // datepicker is open or not, so we have to listen to hide/show events
            // and manually keep track of the 'open' state
            this.__isOpen = false;
        }
    });
    var DateTimeWidget = DateWidget.extend({
        type_of_date: "datetime",
        init: function (parent, options) {
            console.log('Parent DateTime', parent);
            this._super(parent, _.extend({}, options || {}));
        },
    });
//    return {
//        DateWidget: DateWidget,
//        DateTimeWidget: DateTimeWidget,
//    };
});
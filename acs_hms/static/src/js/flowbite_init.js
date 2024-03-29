odoo.define('hms.appointment.init_datepicker', function (require) {
    "use strict";

    var core = require('web.core');
    var FormController = require('web.FormController');

    FormController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            // Initialize your custom date picker here
            $('.custom-datepicker').datepicker(); // Replace 'datepicker()' with the actual initialization method of your custom date picker
        }
    });
});

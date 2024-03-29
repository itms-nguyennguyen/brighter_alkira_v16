$(document).ready(function () {  
    var PatientPortalData = $("input[name='patient_portal_line_graph']").val();

    if (PatientPortalData){
        ACSPatientChartData = JSON.parse(PatientPortalData);
        new Chart(document.getElementById("ACSPatientLineChart"), {
            type: 'line',
            data: ACSPatientChartData,
            options: {
              scales: {
                xAxes: [{
                    ticks: {
                        autoSkip: false,
                        maxRotation: 45,
                        minRotation: 45,
                    }
                }]
              }
            }
        });

    }
});

odoo.define('acs_hms_portal.Many2many_tag', function(require) {
    var PublicWidget = require('web.public.widget');
    var NewData = PublicWidget.Widget.extend({
        selector: '.new-get_data',
        start: function() {
            $('.js-example-basic-multiple').select2();
        },
    });
    PublicWidget.registry.Many2many_tag = NewData;
    return NewData;
});
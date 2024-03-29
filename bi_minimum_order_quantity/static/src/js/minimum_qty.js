odoo.define('bi_minimum_order_quantity.minimum_qty', function(require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var website_sale = require('website_sale.website_sale');
    var publicWidget = require('web.public.widget');
    const session = require('web.session');

    publicWidget.registry.WebsiteSale.include({
        _onClickAddCartJSON: function (ev) {
            this._super.apply(this, arguments);
            this._onClickAddCartMinQtyJSON(ev)
        },
        _onClickAddCartMinQtyJSON: function (event) {
            var qty_input = $(event.currentTarget).closest('.input-group').find("input")
            var qty = qty_input.val();
            var $form_data = $('div.js_product').closest('form');
            var min_qty = $form_data.find("input[name='min_qty']").val();
            if (min_qty > parseFloat(qty || 0)) {
                var qty = $(event.target).closest('form').find('input[name="add_qty"]').val(parseInt(min_qty)).html(parseInt(min_qty));
                $('input[name="add_qty"]').popover({
                    animation: true,
                    title: _t('DENIED'),
                    container: 'body',
                    trigger: 'focus',
                    placement: 'top',
                    html: true,
                    content: _t('Minimum Quantity is '+(min_qty)),
                });
                $('input[name="add_qty"]').popover('show');
                setTimeout(function() {
                    $('input[name="add_qty"]').popover('hide')
                }, 5000);
            }
        

            var line_id = qty_input.attr('data-line-id')
            var min_qty_cart = $('.min_qty_'+line_id+'')

            if($('.js_cart_lines').length) {
                if (!session.is_delete){
                    if (parseInt(min_qty_cart.val()) > parseInt(qty)) {
                        var qty = qty_input.val(min_qty_cart.val()).html(min_qty_cart.val());
                        qty_input.popover({
                            animation: true,
                            title: _t('DENIED'),
                            container: 'body',
                            trigger: 'focus',
                            placement: 'top',
                            html: true,
                            content:  _t('Minimum Quantity is '+(min_qty_cart.val())),
                        });
                        qty_input.popover('show');
                        setTimeout(function() {
                            qty_input.popover('hide')
                        }, 1000);
                    }
                }
            }
        }
    });

    publicWidget.registry.websiteSaleCart.include({
    _onClickDeleteProduct: function (ev) {
        ev.preventDefault();
        session.is_delete = true;
        $(ev.currentTarget).closest('tr').find('.js_quantity').val(0).trigger('change');
    },
});

});;
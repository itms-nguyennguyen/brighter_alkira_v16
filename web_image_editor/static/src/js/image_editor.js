odoo.define('web_image_editor.image_editor', function(require) {
"use strict";
    var AbstractFieldBinary = require('web.basic_fields').AbstractFieldBinary;
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');

    AbstractFieldBinary.include({
        start: function(){
            this._super.apply(this, arguments);
            var self = this;
            if (self.$el.find('.o_edit_file_button').length == 1)
                var ImageEditor = new window.FilerobotImageEditor();
                self.$el.find('.o_edit_file_button').click(function(){
                    setTimeout(function(){
                        $("div[title|='Reset']").css("display", "none");
                        $($('#filerobot-image-editor-root').find('button')[0]).before('<button  class="save_edit_image btn btn-outline-success">Save</button>')
                        $('.save_edit_image').click(function(e){
                            var canvas_1 = $('#filerobot-image-editor_filerobot-image-edit-box')[0]
                            var canvas_2 = $('#filerobot-image-editor_filerobot-shapes-edit-box')[0]
                            var bgctx = canvas_1.getContext('2d');
                            bgctx.drawImage(canvas_2, 0, 0,canvas_1.width,canvas_1.height);
                            canvas_1.download = 'image',
                            canvas_1.href = canvas_1.toDataURL()
                            var dialog = new Dialog(this, {
                                title: _t('Save Changes!'),
                                size: 'medium',
                                $content: $('<div class="mb-3"><label for="recipient-name" class="col-form-label">The original image will be overwritten with the edited image! would you like to confirm?</label></div>'),
                                buttons: [
                                    {
                                        text: _t('Confirm'),
                                        classes: 'btn btn-success confirm_edit_button',
                                        click: function () {
                                            if (canvas_1.href){
                                                var data = (canvas_1.href).split(',')[1];
                                                self._setValue(data);
                                                if(data){
                                                    ImageEditor.close();
                                                }
                                            }
                                            dialog.close();
                                        },
                                    },
                                    {
                                        text: _t('Cancel'),
                                        classes: 'btn btn-outline-danger o_form_button_cancel',
                                        close: true,
                                    }
                                ],
                            }).open();
                            dialog._opened.then(function(){
                                dialog.$modal.css('z-index','99999999999999999999999');
                            });
                        })
                    }, 200);
                    var onopen = ImageEditor.open(`/web/image?model=${self.model}&id=${self.res_id}&field=${self.name}`)
                })
        },
    })
});
/** @odoo-module **/

import { ImageField } from "@web/views/fields/image/image_field";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";

function useUniqueDialog() {
    const displayDialog = useOwnedDialogs();
    let close = null;
    return (...args) => {
        if (close) {
            close();
        }
        close = displayDialog(...args);
    };
}

patch(ImageField.prototype, "GeminateImageField", {
    setup(){
		this._super();
    	this.displayDialog = useUniqueDialog();
    },

    onFileEdit(ev){
    	var self = this
    	ev.stopPropagation()
    	ev.preventDefault()
    	const record = this.props.record
        var ImageEditor = new window.FilerobotImageEditor();
        var onopen = ImageEditor.open(`/web/image?model=${record.resModel}&id=${record.resId}&field=${this.props.id}`)
        setTimeout(function(){
	        $("div[title|='Reset']").css("display", "none");
	        $($('#filerobot-image-editor-root').find('button')[0]).before('<button  class="save_edit_image btn btn-outline-success">Save</button>')
        	$('.save_edit_image').click(function(e){
        		$('#filerobot-image-editor-root').css({'opacity': 0.9})
                var canvas_1 = $('#filerobot-image-editor_filerobot-image-edit-box')[0]
                var canvas_2 = $('#filerobot-image-editor_filerobot-shapes-edit-box')[0]
                var bgctx = canvas_1.getContext('2d');
                bgctx.drawImage(canvas_2, 0, 0,canvas_1.width,canvas_1.height);
                canvas_1.download = 'image',
                canvas_1.href = canvas_1.toDataURL()

        		self.displayDialog(ConfirmationDialog, {
		            title: self.env._t("Save Changes!"),
		            body: self.env._t("The original image will be overwritten with the edited image! would you like to confirm?"),
		            confirm: () => {
                        if (canvas_1.href){
                            var data = (canvas_1.href).split(',')[1];
                            self.props.update(data);
                            if(data){
                                ImageEditor.close();
                            }
                        }
		            },
		            cancel: () => {
		                // `ConfirmationDialog` needs this prop to display the cancel
		                // button but we do nothing on cancel.
                		$('#filerobot-image-editor-root').css({'opacity': 1})
		            },
		        });
        	})
        },100)
    }
})
 
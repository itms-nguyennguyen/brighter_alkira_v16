/** @odoo-module */

import { ImageField } from '@web/views/fields/image/image_field';
import { patch } from "@web/core/utils/patch";
import { isBinarySize } from "@web/core/utils/binary";
import { url } from "@web/core/utils/urls";
import { fileTypeMagicWordMap, imageCacheKey } from "@web/views/fields/image/image_field";
const { DateTime } = luxon;

patch(ImageField.prototype, 'image_field_editor', {
    setup() {
        this._super(...arguments);
    },

    onFileEdit(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        
        var self = this;
        var fileurl = "";

        if (this.state.isValid && this.props.value) {
            if (isBinarySize(this.props.value)) {
                fileurl =  url("/web/image", {
                    model: this.props.record.resModel,
                    id: this.props.record.resId,
                    field: this.props.name,
                    unique: imageCacheKey(this.props.record.data.__last_update),
                });
            }else {
                // Use magic-word technique for detecting image type
                const magic = fileTypeMagicWordMap[this.props.value[0]] || "png";
                fileurl =  `data:image/${magic};base64,${this.props.value}`;
            }
        }

        if (fileurl){
            var ImageEditodiv = document.createElement('div');
            ImageEditodiv.id = 'tui-image-editor';
            ImageEditodiv.style.cssText = 'position: absolute !important'; 
            document.body.appendChild(ImageEditodiv);

            const imageEditor = new tui.ImageEditor('#tui-image-editor', {
                includeUI: {
                    loadImage: {
                        path: fileurl,
                        name: 'Blank'
                    },
                    theme: blackTheme,
                    initMenu: 'filter',
                    menuBarPosition: 'bottom',                        
                },
                selectionStyle: {
                    cornerSize: 20,
                    rotatingPointOffset: 70,
                },
            });
            if (imageEditor){
                var tuiLogo = $('.tui-image-editor-header-logo');
                tuiLogo.hide();

                var btnSave = document.createElement("button");
                btnSave.className = 'tui-image-editor-save-btn';
                btnSave.style.cssText = 'margin-left: 4px !important; background-color: #fff;border: 1px solid #ddd;color: #222;font-family: "Noto Sans", sans-serif;font-size: 12px';
                btnSave.innerHTML = '<span>Save</span>';

                var downloadBtn = $('.tui-image-editor-main-container .tui-image-editor-download-btn')
                $(btnSave).insertAfter(downloadBtn);
                
                $(btnSave).click(function() {
                    var file = {};
                    var data = imageEditor.toDataURL();
                    data = data.split(',')[1];
                    self.props.update(data || false);
                    self.state.isValid = true;
                    self.props.record.save();                    
                    ImageEditodiv.remove();
                    location.reload();
                });
            }
        }
    }
});

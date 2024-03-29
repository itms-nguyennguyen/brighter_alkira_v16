# -*- coding: utf-8 -*-

{
    "name": "Brighter Image Editor",
    "summary": "With the Image Editor that is the perfect combination of simple and beautiful, the Image Editor is a Full-Featured one that is perfect for everyday use.",
    "version": "16.0.1",
    "description": """
        Features
        ======================================
        - Crop, Flip, Rotation, Drawing, Shape, Icon, Text, Mask Filter, Image Filter.
        - Download, Image Load, Undo, Redo, Reset, Delete Object(Shape, Line, Mask Image...).
        - Grayscale, Invert, Sepia, Blur Sharpen, Emboss, RemoveWhite, Brightness, Noise, Pixelate, ColorFilter, Tint, Multiply, Blend.
        - Easy to apply the size and design you want.    
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/image_field_editor.png"],
    "category": "Extra Tools",
    "depends": [
        "base",
        "web",
    ],
    "data": [],
    "assets": {
        "web.assets_backend": [
            # https://github.com/fabricjs/fabric.js/releases #
            "/image_field_editor/static/src/lib/fabric.js",
            
            # https://github.com/nhn/tui.code-snippet/releases/tag/v1.5.0 #
            "/image_field_editor/static/src/lib/tui-code-snippet.js",
            
            # https://github.com/nhn/tui.color-picker/releases/tag/v2.2.6 #
            "/image_field_editor/static/src/lib/tui-color-picker.css",
            "/image_field_editor/static/src/lib/tui-color-picker.js",
            
            # https://uicdn.toast.com/tui-image-editor/latest/tui-image-editor.css #
            "/image_field_editor/static/src/lib/tui-image-editor.css",
            
            # https://uicdn.toast.com/tui-image-editor/latest/tui-image-editor.js #
            "/image_field_editor/static/src/lib/tui-image-editor.js",
            
            # https://github.com/nhn/tui.image-editor/blob/master/apps/image-editor/examples/js/theme/black-theme.js #
            "/image_field_editor/static/src/lib/black-theme.js",
            
            # https://github.com/eligrey/FileSaver.js #
            "/image_field_editor/static/src/lib/FileSaver.js",
            "/image_field_editor/static/src/js/image_field.js",

            "image_field_editor/static/src/xml/image_field.xml",
        ],
    },
    "installable": True,
    "application": True,
    "price"                :  35,
    "currency"             :  "EUR",
}

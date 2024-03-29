{
    "name": "Brighter General",
    "summary": """
        Contain all general extended feature
        """,
    "description": """

    """,
    'category': 'BrighterAPN',
    "summary": "",
    'author': "ITMS Group",
    'website': "https://itmsgroup.com.au",
    "version": "16.3.1",
    # any module necessary for this one to work correctly
    "depends": ["base"],
    # always loaded
    "data": [
        "views/res_config_settings.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "itms_general/static/src/**/*",
            # "itms_general/static/src/css/bootstrap.css",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": True,
}

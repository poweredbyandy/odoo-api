{
    "name": "Allow Iframe Embedding",
    "summary": "Permite que este Odoo sea embebido en un iframe con aislamiento de sesión.",
    "version": "18.0.2.0.3",
    "author": "andyengit",
    "maintainer": "andyengit",
    "category": "Technical",
    "license": "LGPL-3",
    "depends": ["web", "web_tour"],
    "assets": {
        "web.assets_backend": [
            "web_allow_iframe/static/src/js/disable_tours_iframe.js",
        ],
        "web.assets_frontend": [
            "web_allow_iframe/static/src/js/disable_tours_iframe.js",
        ],
    },
    "installable": True,
    "application": False,
}

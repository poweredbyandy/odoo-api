{
    "name": "OAuth Provider",
    "summary": "OAuth servidor (flujo implícito), validación access_token XML-RPC y respaldo IdP auth_oauth. Unifica oauth_provider_xmlrpc_auth y auth_oauth_xmlrpc_token_login.",
    "version": "18.0.1.2.26",
    "author": "andyengit",
    "maintainer": "andyengit",
    "category": "Technical",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "oauth_provider/static/src/js/clipboard_fallback.js",
            "oauth_provider/static/src/js/oauth_embed_debug_boot.js",
            "oauth_provider/static/src/js/oauth_embed_debug.js",
            "oauth_provider/static/src/js/oauth_embed_session.js",
            "oauth_provider/static/src/js/oauth_embed_iframe_router_guard.js",
            "oauth_provider/static/src/js/oauth_embed_rpc_guard.js",
            "oauth_provider/static/src/js/oauth_embed_iframe_guard.js",
        ],
        "web.assets_frontend": [
            "oauth_provider/static/src/js/clipboard_fallback.js",
            "oauth_provider/static/src/js/oauth_embed_debug_boot.js",
            "oauth_provider/static/src/js/oauth_embed_session.js",
        ],
    },
    "installable": True,
    "application": False,
    "post_init_hook": "post_init_hook",
}

from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.http import request


class OAuthProviderHome(Home):
    def _try_embed_session(self):
        return request.env["ir.http"]._try_oauth_embed_token_authentication()

    @http.route()
    def web_client(self, s_action=None, **kw):
        self._try_embed_session()
        try:
            return super().web_client(s_action=s_action, **kw)
        except http.SessionExpiredException:
            if self._try_embed_session() and request.session.uid:
                return super().web_client(s_action=s_action, **kw)
            raise

    @http.route()
    def web_load_menus(self, unique, lang=None):
        self._try_embed_session()
        return super().web_load_menus(unique, lang=lang)

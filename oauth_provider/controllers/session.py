from odoo import http
from odoo.addons.web.controllers.session import Session
from odoo.http import request


class OAuthProviderSession(Session):
    def _revoke_oauth_tokens_for_session_user(self):
        request.env["oauth.provider.token"].sudo().revoke_session_token()

    @http.route("/web/session/logout", type="http", auth="none", readonly=True)
    def logout(self, redirect="/odoo"):
        self._revoke_oauth_tokens_for_session_user()
        return super().logout(redirect=redirect)

    @http.route("/web/session/destroy", type="json", auth="user", readonly=True)
    def destroy(self):
        self._revoke_oauth_tokens_for_session_user()
        return super().destroy()

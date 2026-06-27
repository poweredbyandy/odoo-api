import secrets
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.http import request

PARAM_ACCESS_TOKEN_TTL = "oauth_provider.access_token_ttl_seconds"
DEFAULT_PRACTICAL_NO_EXPIRY_SECONDS = 86400 * 365 * 25
SESSION_OAUTH_ACCESS_TOKEN = "oauth_provider_access_token"


class OauthProviderToken(models.Model):
    _name = "oauth.provider.token"
    _description = "Token OAuth (flujo implícito)"

    token = fields.Char(required=True, index=True)
    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")
    expires = fields.Datetime(required=True)
    session_sid = fields.Char(
        index=True,
        help="Sesión Odoo vinculada al iframe embebido (sin cookie de terceros).",
    )

    @api.model
    def _get_access_token_ttl_seconds(self):
        icp = self.env["ir.config_parameter"].sudo()
        raw = (icp.get_param(PARAM_ACCESS_TOKEN_TTL) or "0").strip()
        try:
            v = int(raw)
        except ValueError:
            v = 0
        if v <= 0:
            return DEFAULT_PRACTICAL_NO_EXPIRY_SECONDS
        return max(60, min(v, 86400 * 365 * 30))

    @api.model
    def _gc_expired(self):
        now = fields.Datetime.now()
        self.sudo().search([("expires", "<", now)]).unlink()

    @api.model
    def create_for_user(self, user, ttl_seconds=None):
        if ttl_seconds is None:
            ttl_seconds = self._get_access_token_ttl_seconds()
        self._gc_expired()
        token = secrets.token_urlsafe(48)
        exp = fields.Datetime.now() + timedelta(seconds=ttl_seconds)
        self.sudo().create(
            {
                "token": token,
                "user_id": user.id,
                "expires": exp,
            }
        )
        return token

    @api.model
    def bind_token_to_session(self, token):
        token = (token or "").strip()
        if not token:
            return
        try:
            request.session[SESSION_OAUTH_ACCESS_TOKEN] = token
            request.session.touch()
            sid = (request.session.sid or "").strip()
            if sid:
                row = self.sudo().search([("token", "=", token)], limit=1)
                if row and row.session_sid != sid:
                    row.write({"session_sid": sid})
        except RuntimeError:
            pass

    @api.model
    def revoke_session_token(self):
        try:
            token = (request.session.get(SESSION_OAUTH_ACCESS_TOKEN) or "").strip()
            if token:
                self.sudo().search([("token", "=", token)]).unlink()
            request.session.pop(SESSION_OAUTH_ACCESS_TOKEN, None)
            request.session.touch()
        except RuntimeError:
            pass

    @api.model
    def mint_web_session_token_for_login(self, login):
        if not self.env.user._is_system():
            raise AccessError(
                _("Solo administradores pueden emitir tokens de sesión OAuth.")
            )
        key = (login or "").strip()
        if not key:
            return False
        user = self.env["res.users"].sudo().search([("login", "=", key)], limit=1)
        if not user:
            return False
        return self.create_for_user(user)

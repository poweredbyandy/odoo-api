from odoo import fields, models
from odoo.exceptions import AccessDenied

from .oauth_token_validation import oauth_provider_validate_access_token_for_xmlrpc


class ResUsers(models.Model):
    _inherit = "res.users"

    def _oauth_provider_check_embed_token(self, token):
        token = (token or "").strip()
        if not token or not self.active:
            raise AccessDenied()
        tok_model = self.env["oauth.provider.token"].sudo()
        tok_model._gc_expired()
        row = tok_model.search(
            [
                ("token", "=", token),
                ("user_id", "=", self.id),
            ],
            limit=1,
        )
        if not row or row.expires < fields.Datetime.now():
            raise AccessDenied()
        return {
            "uid": self.id,
            "auth_method": "oauth_provider_embed",
            "mfa": "default",
        }

    def _check_credentials(self, credential, env):
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            cred_type = credential.get("type")
            if cred_type == "oauth_provider_embed":
                return self._oauth_provider_check_embed_token(credential.get("token"))
            if cred_type != "password":
                raise
            token = credential.get("password") or ""
            if len(token) < 10:
                raise
            user = self.env.user
            if not user.ids:
                raise AccessDenied()
            try:
                val = oauth_provider_validate_access_token_for_xmlrpc(user, token)
            except AccessDenied:
                raise
            except Exception:
                raise AccessDenied() from None
            v_login = (val.get("user_id") or "").strip().lower()
            email = (val.get("email") or "").strip().lower()
            if v_login != user.login.lower():
                if not email or (user.email or "").lower() != email:
                    raise AccessDenied()
            return {
                "uid": user.id,
                "auth_method": "oauth_token",
                "mfa": "default",
            }

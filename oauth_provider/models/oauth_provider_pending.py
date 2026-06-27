import json
import secrets
from datetime import timedelta

from odoo import api, fields, models


class OauthProviderPending(models.Model):
    _name = "oauth.provider.pending"
    _description = "Parámetros OAuth authorize cuando la sesión puede reiniciarse"

    token = fields.Char(required=True, index=True)
    payload_json = fields.Text(required=True)
    expires = fields.Datetime(required=True)

    _sql_constraints = [
        ("oauth_provider_pending_token_unique", "unique(token)", "Token pending duplicado."),
    ]

    @api.model
    def _gc_expired(self):
        now = fields.Datetime.now()
        self.sudo().search([("expires", "<", now)]).unlink()

    @api.model
    def create_from_payload(self, payload, ttl_seconds=600):
        self._gc_expired()
        token = secrets.token_urlsafe(32)
        self.sudo().create(
            {
                "token": token,
                "payload_json": json.dumps(payload),
                "expires": fields.Datetime.now() + timedelta(seconds=ttl_seconds),
            }
        )
        return token

    @api.model
    def consume(self, token):
        if not token or not str(token).strip():
            return None
        self._gc_expired()
        row = self.sudo().search([("token", "=", token.strip())], limit=1)
        if not row:
            return None
        now = fields.Datetime.now()
        if row.expires < now:
            row.unlink()
            return None
        try:
            data = json.loads(row.payload_json)
        except json.JSONDecodeError:
            row.unlink()
            return None
        row.unlink()
        return data if isinstance(data, dict) else None

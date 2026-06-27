import uuid
from urllib.parse import urlparse

from odoo import api, fields, models


def _origin_tuple(parsed):
    if not parsed.hostname:
        return None
    port = parsed.port
    if port is None:
        port = 443 if (parsed.scheme or "").lower() == "https" else 80
    return (parsed.scheme.lower(), parsed.hostname.lower(), port)


def _is_loopback_host(hostname):
    if not hostname:
        return False
    h = hostname.lower()
    return h in ("localhost", "127.0.0.1", "::1") or h.startswith("127.")


def _origins_equivalent(oa, ob):
    if oa is None or ob is None:
        return False
    if oa == ob:
        return True
    if oa[0] != ob[0] or oa[2] != ob[2]:
        return False
    ha, hb = oa[1], ob[1]
    if ha == hb:
        return True
    if _is_loopback_host(ha) and _is_loopback_host(hb):
        return True
    return False


class OauthProviderClient(models.Model):
    _name = "oauth.provider.client"
    _description = "Cliente OAuth para Odoo Origen"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    client_id = fields.Char(
        string="ID de cliente (para el Odoo Origen)",
        required=True,
        copy=False,
        index=True,
        default=lambda self: uuid.uuid4().hex,
        help="Cópielo en el Origen: Ajustes → OAuth Odoo Client → ID de cliente OAuth. "
        "Se genera al guardar el registro.",
    )
    redirect_uris = fields.Text(
        string="URIs de retorno",
        help="Una URL absoluta por línea. Debe ser la del Odoo Origen (no la de este servidor), "
        "por ejemplo http://localhost:8069/auth_oauth/signin si el Origen corre en el puerto 8069.",
    )

    _sql_constraints = [
        (
            "oauth_provider_client_id_unique",
            "unique(client_id)",
            "El ID de cliente debe ser único.",
        ),
    ]

    def _normalize_lines(self):
        self.ensure_one()
        lines = []
        for line in (self.redirect_uris or "").splitlines():
            s = line.strip()
            if s:
                lines.append(s)
        return lines

    def is_redirect_allowed(self, uri):
        self.ensure_one()
        if not uri:
            return False
        lines = self._normalize_lines()
        if uri in lines:
            return True
        pu = urlparse(uri)
        ou = _origin_tuple(pu)
        if not ou:
            return False
        for line in lines:
            pl = urlparse(line)
            lo = _origin_tuple(pl)
            if lo and ou and _origins_equivalent(lo, ou):
                return True
        return False

    @api.model
    def get_by_client_id(self, client_id):
        if not client_id:
            return self.browse()
        return self.search([("client_id", "=", client_id), ("active", "=", True)], limit=1)

import requests
from werkzeug import http, datastructures

from odoo import fields
from odoo.exceptions import AccessDenied

if hasattr(datastructures.WWWAuthenticate, "from_header"):
    parse_auth = datastructures.WWWAuthenticate.from_header
else:
    parse_auth = http.parse_www_authenticate_header


def oauth_provider_tokeninfo_rpc(env, endpoint, access_token):
    icp = env["ir.config_parameter"].sudo()
    if icp.get_param("auth_oauth.authorization_header"):
        response = requests.get(
            endpoint,
            headers={"Authorization": "Bearer %s" % access_token},
            timeout=10,
        )
    else:
        response = requests.get(
            endpoint,
            params={"access_token": access_token},
            timeout=10,
        )
    if response.ok:
        return response.json()
    auth_challenge = parse_auth(response.headers.get("WWW-Authenticate"))
    if auth_challenge and auth_challenge.type == "bearer" and "error" in auth_challenge:
        return dict(auth_challenge)
    return {"error": "invalid_request"}


def oauth_provider_auth_oauth_fallback_payload(user, access_token):
    """Si auth_oauth está instalado y el token valida para el oauth_uid del usuario."""
    if not user.oauth_provider_id or not user.oauth_uid:
        return None
    Users = user.env["res.users"]
    if not hasattr(Users, "_auth_oauth_validate"):
        return None
    try:
        validation = Users._auth_oauth_validate(
            user.oauth_provider_id.id,
            access_token,
        )
    except Exception:
        return None
    subj = str(validation.get("user_id", "")).strip().lower()
    ouid = str(user.oauth_uid or "").strip().lower()
    if not ouid or subj != ouid:
        return None
    return {
        "user_id": user.login,
        "email": (user.email or user.login or ""),
    }


def oauth_provider_validate_access_token_for_xmlrpc(user, access_token):
    """Valida token: tabla local, /oauth_provider/tokeninfo, o respaldo vía auth_oauth."""
    env = user.env
    Token = env["oauth.provider.token"].sudo()
    now = fields.Datetime.now()
    row = Token.search(
        [
            ("token", "=", access_token),
            ("expires", ">=", now),
        ],
        limit=1,
    )
    if row:
        if row.user_id.id != user.id:
            raise AccessDenied()
        return {
            "user_id": user.login,
            "email": (user.email or user.login or ""),
        }
    icp = env["ir.config_parameter"].sudo()
    base = (icp.get_param("web.base.url") or "").strip().rstrip("/")
    if not base:
        val = oauth_provider_auth_oauth_fallback_payload(user, access_token)
        if val:
            return val
        raise AccessDenied()
    endpoint = "%s/oauth_provider/tokeninfo" % base
    validation = oauth_provider_tokeninfo_rpc(env, endpoint, access_token)
    if validation.get("error"):
        val = oauth_provider_auth_oauth_fallback_payload(user, access_token)
        if val:
            return val
        raise AccessDenied()
    subject = next(
        filter(
            None,
            [
                validation.get("sub"),
                validation.get("id"),
                validation.get("user_id"),
            ],
        ),
        None,
    )
    if not subject:
        val = oauth_provider_auth_oauth_fallback_payload(user, access_token)
        if val:
            return val
        raise AccessDenied()
    return {
        "user_id": str(subject).strip(),
        "email": (validation.get("email") or "").strip().lower(),
    }

from urllib.parse import parse_qs, urlparse

from odoo import api, fields, http, models
from odoo.http import request, root
from odoo.service import security

from .oauth_provider_token import SESSION_OAUTH_ACCESS_TOKEN

EMBED_TOKEN_HEADER = "X-OAuth-Embed-Token"
EMBED_DB_HEADER = "X-OAuth-Embed-Db"


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _oauth_embed_token_from_request(cls):
        httpreq = request.httprequest
        token = httpreq.headers.get(EMBED_TOKEN_HEADER) or httpreq.args.get(
            "oauth_embed_token"
        )
        if token:
            return token.strip()
        referer = (httpreq.headers.get("Referer") or "").strip()
        if referer:
            try:
                parsed = urlparse(referer)
                token = (parse_qs(parsed.query).get("oauth_embed_token") or [""])[0]
            except Exception:
                token = ""
        return (token or "").strip()

    @classmethod
    def _oauth_embed_resolve_dbname(cls):
        httpreq = request.httprequest
        db = request.session.db
        if db and db in http.db_filter([db]):
            return db
        qdb = (
            httpreq.headers.get(EMBED_DB_HEADER) or httpreq.args.get("db") or ""
        ).strip()
        if not qdb:
            referer = (httpreq.headers.get("Referer") or "").strip()
            if referer:
                try:
                    parsed = urlparse(referer)
                    qdb = (parse_qs(parsed.query).get("db") or [""])[0].strip()
                except Exception:
                    qdb = ""
        if qdb and qdb in http.db_filter([qdb]):
            request.session.db = qdb
            request.session.is_dirty = True
            return qdb
        all_dbs = http.db_list(force=True)
        if len(all_dbs) == 1:
            request.session.db = all_dbs[0]
            request.session.is_dirty = True
            return all_dbs[0]
        return None

    @classmethod
    def _oauth_embed_lookup_token_row(cls, token):
        if not token:
            return request.env["oauth.provider.token"]
        tok_model = request.env["oauth.provider.token"].sudo()
        tok_model._gc_expired()
        row = tok_model.search([("token", "=", token)], limit=1)
        now = fields.Datetime.now()
        if not row or row.expires < now:
            return request.env["oauth.provider.token"]
        user = row.user_id
        if not user or not user.active:
            return request.env["oauth.provider.token"]
        return row

    @classmethod
    def _oauth_embed_restore_session_for_token(cls, row):
        sid = (row.session_sid or "").strip()
        if not sid or not root.session_store.is_valid_key(sid):
            return False
        if request.session.sid == sid:
            if (
                request.session.uid == row.user_id.id
                and security.check_session(request.session, request.env, request)
            ):
                return True
        stored = root.session_store.get(sid)
        if not stored:
            return False
        if (stored.get(SESSION_OAUTH_ACCESS_TOKEN) or "").strip() != row.token:
            return False
        if stored.uid and stored.uid != row.user_id.id:
            return False
        request.session = stored
        request.session.sid = sid
        return True

    @classmethod
    def _oauth_embed_token_csrf_trusted(cls):
        token = cls._oauth_embed_token_from_request()
        row = cls._oauth_embed_lookup_token_row(token)
        if not row:
            return False
        if request.session.uid != row.user_id.id:
            return False
        return security.check_session(request.session, request.env, request)

    @classmethod
    def _try_oauth_embed_token_authentication(cls):
        token = cls._oauth_embed_token_from_request()
        if not token:
            return False
        dbname = cls._oauth_embed_resolve_dbname()
        if not dbname:
            return False
        row = cls._oauth_embed_lookup_token_row(token)
        if not row:
            return False
        user = row.user_id
        cls._oauth_embed_restore_session_for_token(row)
        if request.session.uid == user.id:
            request.update_env(user=user.id)
            if security.check_session(request.session, request.env, request):
                row.bind_token_to_session(token)
                return False
        elif request.session.uid is not None:
            request.session.logout(keep_db=True)
            request.env = api.Environment(
                request.env.cr, None, request.session.context
            )
        session = request.session
        session.db = dbname
        session.login = user.login
        session.uid = user.id
        session.context = dict(user.with_user(user).context_get())
        session.session_token = user._compute_session_token(session.sid)
        session._trace_disable = True
        session.is_dirty = True
        row.bind_token_to_session(token)
        request.update_env(user=user.id)
        return True

    @classmethod
    def _authenticate_explicit(cls, auth):
        cls._try_oauth_embed_token_authentication()
        return super()._authenticate_explicit(auth)

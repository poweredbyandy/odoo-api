import logging

_logger = logging.getLogger(__name__)


def patch_request_validate_csrf_for_embed():
    from odoo.http import Request

    if getattr(Request.validate_csrf, "_oauth_embed_patched", False):
        return

    _orig_validate_csrf = Request.validate_csrf

    def validate_csrf(self, csrf):
        if _orig_validate_csrf(self, csrf):
            return True
        if not self.db or not self.registry:
            return False
        try:
            ir_http = self.registry["ir.http"]
            token = ir_http._oauth_embed_token_from_request()
            row = ir_http._oauth_embed_lookup_token_row(token)
            if row:
                ir_http._oauth_embed_restore_session_for_token(row)
                self.update_env(user=row.user_id.id)
            if ir_http._oauth_embed_token_csrf_trusted():
                return True
        except Exception:
            _logger.debug(
                "oauth_provider: comprobación CSRF embebida falló",
                exc_info=True,
            )
        return False

    validate_csrf._oauth_embed_patched = True
    Request.validate_csrf = validate_csrf

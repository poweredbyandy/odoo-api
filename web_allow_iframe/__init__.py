from . import models
from odoo.http import HTTPRequest

_original_http_request_init = HTTPRequest.__init__


def _patched_http_request_init(self, environ):
    _original_http_request_init(self, environ)
    try:
        alt_sid = self.cookies.get("session_id_h")
        if alt_sid:
            self._session_id__ = alt_sid
    except Exception:
        pass


HTTPRequest.__init__ = _patched_http_request_init

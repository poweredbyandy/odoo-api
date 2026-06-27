from urllib.parse import urlparse

from odoo import models
from odoo.http import request


def _host_label(httprequest):
    return (httprequest.host or "").split(":")[0].lower()


def _is_loopback_host(hostname):
    if not hostname:
        return False
    return hostname in ("localhost", "127.0.0.1", "::1") or hostname.startswith("127.")


def _origins_different(url_a, url_b):
    pa, pb = urlparse(url_a), urlparse(url_b)
    if not pa.netloc or not pb.netloc:
        return False
    return pa.netloc.lower() != pb.netloc.lower()


class IrHttpIframe(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _request_is_iframe_embed(cls):
        httpreq = request.httprequest
        dest = (httpreq.headers.get("Sec-Fetch-Dest") or "").lower()
        if dest in ("iframe", "nested-navigate"):
            return True
        referer = httpreq.headers.get("Referer") or ""
        if referer and _origins_different(referer, httpreq.url_root):
            return True
        path = httpreq.path or ""
        if path.startswith("/oauth_provider/embed_login") or path.startswith(
            "/oauth_provider/web_session"
        ):
            return True
        return False

    @classmethod
    def _cookie_secure_allowed(cls):
        httpreq = request.httprequest
        if (httpreq.scheme or "").lower() == "https":
            return True
        return _is_loopback_host(_host_label(httpreq))

    @classmethod
    def _patch_session_cookie_for_iframe(cls, cookie):
        if not cookie.startswith("session_id="):
            return cookie
        if (request.httprequest.scheme or "").lower() != "https":
            return cookie
        if "SameSite" not in cookie:
            cookie += "; SameSite=None"
        else:
            cookie = cookie.replace("SameSite=Lax", "SameSite=None").replace(
                "SameSite=Strict", "SameSite=None"
            )
        if "Secure" not in cookie:
            cookie += "; Secure"
        if "Partitioned" not in cookie:
            cookie += "; Partitioned"
        return cookie

    @classmethod
    def _post_dispatch(cls, response):
        super()._post_dispatch(response)
        if not hasattr(response, "headers"):
            return

        response.headers.pop("X-Frame-Options", None)

        csp = response.headers.get("Content-Security-Policy", "")
        if "frame-ancestors" in csp:
            parts = [
                d.strip()
                for d in csp.split(";")
                if "frame-ancestors" not in d
            ]
            parts.append("frame-ancestors *")
            response.headers["Content-Security-Policy"] = "; ".join(
                p for p in parts if p
            )

        if not cls._request_is_iframe_embed():
            return

        cookies_raw = response.headers.getlist("Set-Cookie")
        if not cookies_raw:
            return
        patched = []
        for cookie in cookies_raw:
            if cookie.startswith("session_id="):
                cookie = cls._patch_session_cookie_for_iframe(cookie)
            patched.append(cookie)
        response.headers.remove("Set-Cookie")
        for cookie in patched:
            response.headers.add("Set-Cookie", cookie)

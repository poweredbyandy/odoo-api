import json

from odoo.tests import TransactionCase, tagged

from odoo.addons.oauth_provider.controllers.main import (
    _effective_oauth_redirect_uri,
    _origins_equivalent,
    _origin_tuple,
    _parse_oauth_state_dict,
    _same_loopback_machine,
    _signin_url_from_oauth_state,
)


@tagged("post_install", "-at_install", "oauth_provider")
class TestOauthProviderHelpers(TransactionCase):
    def test_parse_state_double_encoded_r(self):
        state = '{"d":"db","p":4,"r":"http%253A%252F%252Flocalhost%253A8069%252Fweb"}'
        self.assertIsNotNone(_parse_oauth_state_dict(state))
        url = _signin_url_from_oauth_state(state)
        self.assertEqual(url, "http://localhost:8069/auth_oauth/signin")

    def test_signin_url_from_state(self):
        state = json.dumps(
            {
                "d": "db",
                "p": 4,
                "r": "http%3A%2F%2Flocalhost%3A8069%2Fweb",
            }
        )
        url = _signin_url_from_oauth_state(state)
        self.assertEqual(url, "http://localhost:8069/auth_oauth/signin")

    def test_same_loopback_localhost_vs_127(self):
        self.assertTrue(
            _same_loopback_machine(
                "http://localhost:8071/auth_oauth/signin",
                "http://127.0.0.1:8071/",
            )
        )

    def test_origin_tuple(self):
        from urllib.parse import urlparse

        self.assertEqual(
            _origin_tuple(urlparse("http://localhost:8069/foo")),
            ("http", "localhost", 8069),
        )

    def test_effective_oauth_redirect_uri_homolog_redirect_state_origen(self):
        fixed = "http://localhost:8069/auth_oauth/signin"
        fix_o = ("http", "localhost", 8069)
        hom_o = ("http", "localhost", 8071)
        redirect_uri = "http://localhost:8071/auth_oauth/signin"
        eff, relax = _effective_oauth_redirect_uri(redirect_uri, fixed, fix_o, hom_o)
        self.assertEqual(eff, "http://localhost:8069/auth_oauth/signin")
        self.assertTrue(relax)

    def test_effective_oauth_redirect_uri_loopback_vs_localhost_homolog(self):
        fixed = "http://localhost:8069/auth_oauth/signin"
        fix_o = ("http", "localhost", 8069)
        hom_o = ("http", "127.0.0.1", 8071)
        redirect_uri = "http://127.0.0.1:8071/auth_oauth/signin"
        eff, relax = _effective_oauth_redirect_uri(redirect_uri, fixed, fix_o, hom_o)
        self.assertEqual(eff, "http://localhost:8069/auth_oauth/signin")
        self.assertTrue(relax)

    def test_origins_equivalent_localhost_127(self):
        a = ("http", "localhost", 8069)
        b = ("http", "127.0.0.1", 8069)
        self.assertTrue(_origins_equivalent(a, b))
        self.assertFalse(_origins_equivalent(a, ("http", "127.0.0.1", 8071)))

    def test_effective_oauth_redirect_uri_origen_coherent(self):
        fixed = "http://localhost:8069/auth_oauth/signin"
        fix_o = ("http", "localhost", 8069)
        hom_o = ("http", "localhost", 8071)
        redirect_uri = "http://localhost:8069/auth_oauth/signin"
        eff, relax = _effective_oauth_redirect_uri(redirect_uri, fixed, fix_o, hom_o)
        self.assertEqual(eff, redirect_uri)
        self.assertTrue(relax)

    def test_effective_oauth_redirect_uri_sin_origen_en_state(self):
        fixed = "http://localhost:8071/auth_oauth/signin"
        fix_o = ("http", "localhost", 8071)
        hom_o = ("http", "localhost", 8071)
        redirect_uri = "http://localhost:8071/auth_oauth/signin"
        eff, relax = _effective_oauth_redirect_uri(redirect_uri, fixed, fix_o, hom_o)
        self.assertEqual(eff, redirect_uri)
        self.assertFalse(relax)

    def test_effective_state_homolog_localhost_vs_127_same_origin(self):
        fixed = "http://127.0.0.1:8071/auth_oauth/signin"
        fix_o = ("http", "127.0.0.1", 8071)
        hom_o = ("http", "localhost", 8071)
        redirect_uri = "http://localhost:8071/auth_oauth/signin"
        eff, relax = _effective_oauth_redirect_uri(redirect_uri, fixed, fix_o, hom_o)
        self.assertEqual(eff, redirect_uri)
        self.assertFalse(relax)


@tagged("post_install", "-at_install", "oauth_provider")
class TestOauthProviderClientModel(TransactionCase):
    def test_is_redirect_allowed_same_origin(self):
        client = self.env["oauth.provider.client"].create(
            {
                "name": "Test",
                "redirect_uris": "http://localhost:8069/web",
            }
        )
        self.assertTrue(
            client.is_redirect_allowed("http://localhost:8069/auth_oauth/signin")
        )
        self.assertFalse(
            client.is_redirect_allowed("http://localhost:8071/auth_oauth/signin")
        )

    def test_is_redirect_allowed_loopback_alias(self):
        client = self.env["oauth.provider.client"].create(
            {
                "name": "Loopback",
                "redirect_uris": "http://localhost:8069/web",
            }
        )
        self.assertTrue(
            client.is_redirect_allowed("http://127.0.0.1:8069/auth_oauth/signin")
        )


@tagged("post_install", "-at_install", "oauth_provider")
class TestOauthProviderPending(TransactionCase):
    def test_consume_returns_payload_and_deletes(self):
        Pending = self.env["oauth.provider.pending"].sudo()
        payload = {
            "response_type": "token",
            "client_id": "abc",
            "redirect_uri": "http://x/y",
            "scope": "openid",
            "state": "{}",
        }
        token = Pending.create_from_payload(payload)
        self.assertTrue(token)
        got = Pending.consume(token)
        self.assertEqual(got, payload)
        self.assertFalse(Pending.search([("token", "=", token)]))
        self.assertIsNone(Pending.consume(token))

    def test_consume_unknown_returns_none(self):
        Pending = self.env["oauth.provider.pending"].sudo()
        self.assertIsNone(Pending.consume("no-existe"))

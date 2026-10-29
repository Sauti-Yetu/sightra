from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase, override_settings

from apps.accounts.oauth import pkce_pair, public_absolute_uri
from apps.accounts.services.supabase_client import oauth_authorize_url


class PkceTests(SimpleTestCase):
    def test_pkce_pair_shape(self):
        verifier, challenge = pkce_pair()
        self.assertGreaterEqual(len(verifier), 40)
        self.assertNotIn("=", challenge)
        self.assertNotEqual(verifier, challenge)

    @patch.dict(
        "os.environ",
        {"SUPABASE_URL": "https://abc.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "anon"},
        clear=False,
    )
    def test_authorize_url_includes_pkce(self):
        url = oauth_authorize_url(
            "google",
            "https://sightra.net/auth/callback/",
            code_challenge="abc123",
        )
        self.assertIn("provider=google", url)
        self.assertIn("code_challenge=abc123", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("redirect_to=", url)


class PublicUrlTests(SimpleTestCase):
    @override_settings()
    @patch.dict("os.environ", {"SIGHTTRA_PUBLIC_URL": "https://sightra.net"}, clear=False)
    def test_configured_public_url(self):
        class Req:
            META = {}

            def build_absolute_uri(self, path):
                return "http://localhost" + path

        self.assertEqual(public_absolute_uri(Req(), "/auth/callback/"), "https://sightra.net/auth/callback/")


class GoogleAuthViewTests(TestCase):
    @patch("apps.accounts.views.build_google_authorize_url", return_value=None)
    def test_unconfigured_google_redirects_home_to_signin(self, _mock):
        client = Client()
        res = client.get("/auth/google/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/signin/", res.url)

    @patch(
        "apps.accounts.views.build_google_authorize_url",
        return_value="https://abc.supabase.co/auth/v1/authorize?provider=google",
    )
    def test_google_redirects_to_provider(self, _mock):
        client = Client()
        res = client.get("/auth/google/?next=/reader/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("provider=google", res.url)

    def test_callback_without_code_renders_waiter(self):
        client = Client()
        res = client.get("/auth/callback/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Completing sign-in")

    def test_callback_error_returns_to_signin(self):
        client = Client()
        res = client.get("/auth/callback/?error=access_denied")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/signin/", res.url)

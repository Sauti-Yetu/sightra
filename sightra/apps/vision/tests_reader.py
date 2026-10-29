from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import Client, SimpleTestCase, TestCase

from apps.core.feature_flags import ACTIVE_NAV, HIDDEN_NAV
from apps.vision.reader_service import _parse_model_text


class ReaderNavTests(SimpleTestCase):
    def test_primary_nav_shows_reader_not_masked_tools(self):
        html = render_to_string("bottom_nav.html")
        self.assertIn("/reader/", html)
        self.assertIn("Reader", html)
        self.assertNotIn("/live-map/", html)
        self.assertNotIn("/live-call/", html)
        self.assertNotIn("/voice_assistant/", html)

    def test_feature_flags(self):
        self.assertEqual(ACTIVE_NAV, ("home", "vision", "reader", "settings"))
        self.assertIn("map", HIDDEN_NAV)

    def test_reader_copy_has_no_competitor_name(self):
        html = render_to_string("reader.html")
        self.assertNotIn("Lookout", html)
        self.assertNotIn("lookout", html)


class ReaderParseTests(SimpleTestCase):
    def test_json_payload(self):
        parsed = _parse_model_text('{"spoken": "Five dollars.", "text": "USD 5"}')
        self.assertEqual(parsed["spoken"], "Five dollars.")
        self.assertEqual(parsed["text"], "USD 5")

    def test_plain_text_fallback(self):
        parsed = _parse_model_text("Hello sign\n\nEXIT")
        self.assertEqual(parsed["spoken"], "Hello sign")
        self.assertEqual(parsed["text"], "EXIT")


class ReaderApiTests(TestCase):
    def test_reader_page_requires_sign_in(self):
        client = Client()
        res = client.get("/reader/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/signin/", res.url)

    def test_analyze_requires_consent(self):
        client = Client()
        res = client.post(
            "/api/vision/reader/analyze/",
            data={"frame_data": "data:image/jpeg;base64,aaaa", "mode": "live"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "consent_required")

    def test_analyze_invalid_json(self):
        client = Client()
        res = client.post(
            "/api/vision/reader/analyze/",
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    @patch("apps.vision.views.has_camera_consent", return_value=True)
    @patch("apps.vision.views.has_privacy_notice_ack", return_value=True)
    @patch(
        "apps.vision.views.analyze_reader_image",
        return_value={
            "success": True,
            "spoken": "Exit sign ahead.",
            "text": "EXIT",
            "mode": "signage",
            "language": "en",
        },
    )
    def test_analyze_success(self, _analyze, _ack, _cam):
        client = Client()
        res = client.post(
            "/api/vision/reader/analyze/",
            data={"frame_data": "data:image/jpeg;base64,aaaa", "mode": "signage", "language": "en"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["spoken"], "Exit sign ahead.")

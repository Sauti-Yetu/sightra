import inspect
from unittest.mock import MagicMock, patch

from django.test import Client, SimpleTestCase, TestCase

from apps.accounts.services.session_service import display_name_for
from apps.core.services import GeminiAnalyzer
from apps.core.views import _display_name_for, dashboard


class LandingAndManifestTests(TestCase):
    def test_landing_focuses_on_vision_and_reader(self):
        client = Client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "See more. Understand more.")
        self.assertContains(res, "Get started")
        self.assertContains(res, "Explore Sightra")
        self.assertContains(res, "Open Vision")
        self.assertContains(res, "Open Reader")
        self.assertContains(res, "Sauti Yetu Assistive Venture")
        self.assertContains(res, "Always use your established mobility aids")
        self.assertContains(res, "app-icon-192.png")
        self.assertContains(res, "sightra-logo.png")
        self.assertNotContains(res, "optional volunteer video")
        self.assertNotContains(res, "offline-ready")
        self.assertNotContains(res, "No hidden fees")
        self.assertNotContains(res, "How Sightra works")
        self.assertNotContains(res, "In development")

    def test_manifest_uses_square_logo_icons(self):
        client = Client()
        res = client.get("/manifest.webmanifest")
        self.assertEqual(res.status_code, 200)
        body = b"".join(res.streaming_content).decode("utf-8")
        self.assertIn("app-icon-192.png", body)
        self.assertIn("app-icon-512.png", body)
        self.assertIn('"name": "Sightra"', body)
        self.assertIn('"background_color": "#000000"', body)
        self.assertNotIn("Lookout", body)


class GeminiHelperTests(SimpleTestCase):
    def tearDown(self):
        import apps.core.gemini as gemini

        gemini._working_model = None
        gemini._configured = False

    def test_generate_text_falls_back_to_next_model(self):
        import apps.core.gemini as gemini

        gemini._working_model = None
        gemini._configured = True
        bad = MagicMock()
        bad.generate_content.side_effect = RuntimeError("404")
        good = MagicMock()
        good.generate_content.return_value = MagicMock(text="Person ahead.")

        with patch("apps.core.gemini.genai.GenerativeModel", side_effect=[bad, good]):
            text = gemini.generate_text(["hello"], timeout=5)

        self.assertEqual(text, "Person ahead.")
        self.assertEqual(gemini._working_model, gemini.GEMINI_MODELS[1])

    def test_generate_text_stops_after_max_attempts(self):
        import apps.core.gemini as gemini

        gemini._working_model = None
        gemini._configured = True
        boom = MagicMock()
        boom.generate_content.side_effect = RuntimeError("404")

        with patch("apps.core.gemini.genai.GenerativeModel", return_value=boom) as ctor:
            with self.assertRaises(RuntimeError):
                gemini.generate_text(["hello"], timeout=1, max_attempts=2)

        self.assertEqual(ctor.call_count, 2)

    def test_analyze_scene_sends_image_and_returns_text(self):
        analyzer = GeminiAnalyzer()
        analyzer.ready = True
        analyzer._last_call_time = 0
        with patch("apps.core.gemini.generate_text", return_value="A chair is blocking the path.") as gen:
            result = analyzer.analyze_scene(
                {"objects": []},
                "What is ahead?",
                force_refresh=True,
                image="fake-image",
            )
        self.assertEqual(result, "A chair is blocking the path.")
        parts = gen.call_args[0][0]
        self.assertIn("fake-image", parts)

    def test_analyze_scene_falls_back_to_objects(self):
        analyzer = GeminiAnalyzer()
        analyzer.ready = True
        with patch("apps.core.gemini.generate_text", side_effect=RuntimeError("down")):
            result = analyzer.analyze_scene(
                {
                    "objects": [
                        {"label": "person", "position": "ahead", "distance_band": "near"}
                    ]
                },
                force_refresh=True,
            )
        self.assertIn("person", result)


class VisionFastPathTests(SimpleTestCase):
    @patch("apps.core.tasks.analyzer.analyze_scene")
    @patch("apps.core.tasks.process_frame_vision_pipeline")
    def test_fast_scan_returns_objects_without_waiting_on_gemini(self, pipeline, analyze_scene):
        from apps.core.tasks import analyze_frame_context

        pipeline.return_value = {
            "objects": [{"label": "person", "position": "ahead", "distance_band": "near"}],
            "warnings": [],
            "hazard_alert": None,
            "detector_ready": True,
        }
        result = analyze_frame_context("frame", narration_mode="fast")
        analyze_scene.assert_not_called()
        self.assertEqual(result["narration_mode"], "fast")
        self.assertIn("person", result["analysis_text"].lower())


class DisplayNameTests(SimpleTestCase):
    def test_given_name_preferred(self):
        self.assertEqual(
            display_name_for({"email": "x@example.com", "user_metadata": {"given_name": "Ada Lovelace"}}),
            "Ada",
        )

    def test_email_local_part(self):
        self.assertEqual(display_name_for({"email": "antonriziki@gmail.com"}), "Antonriziki")

    def test_missing_user(self):
        self.assertEqual(display_name_for(None), "")
        self.assertEqual(display_name_for({}), "")

    def test_dashboard_helper_matches_session_helper(self):
        samples = (
            None,
            {},
            {"email": "ben@example.com"},
            {"email": "x@example.com", "user_metadata": {"given_name": "Ada Lovelace"}},
        )
        for sample in samples:
            self.assertEqual(_display_name_for(sample), display_name_for(sample))


class DashboardTests(TestCase):
    def test_requires_sign_in(self):
        res = Client().get("/dashboard")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/signin/", res.url)

    def _dashboard(self, user):
        with patch("apps.accounts.middleware.SessionService.get_user", return_value=user):
            return Client().get("/dashboard")

    def test_user_a_sees_own_workspace_not_email_or_subscription(self):
        res = self._dashboard({"id": "user-a", "email": "alice.ngugi@example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Welcome back, Alice")
        self.assertContains(res, "What would you like help with today?")
        self.assertContains(res, "Start scan")
        self.assertContains(res, 'href="/vision/"')
        self.assertContains(res, "Open Reader")
        self.assertContains(res, 'href="/reader/"')
        self.assertContains(res, "Voice assistance")
        self.assertContains(res, "/settings/#voice")
        self.assertContains(res, "Voice settings")
        self.assertContains(res, 'href="/signout/"')
        self.assertContains(res, "Account settings")
        self.assertNotContains(res, "alice.ngugi@example.com")
        self.assertNotContains(res, "No hidden fees")
        self.assertNotContains(res, ">Free<")
        self.assertNotContains(res, "Tools ready when you are")
        self.assertNotContains(res, "does not show scan or reading history")

    def test_user_b_does_not_see_user_a_name(self):
        res = self._dashboard({"id": "user-b", "email": "ben@example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Ben")
        self.assertNotContains(res, "Alice")
        self.assertNotContains(res, "alice.ngugi@example.com")

    def test_missing_profile_still_renders_workspace(self):
        res = self._dashboard({"id": "user-c"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Welcome back")
        self.assertContains(res, "Start scan")
        self.assertContains(res, "Open Reader")

    def test_legacy_session_payload_without_display_name(self):
        res = self._dashboard({"id": "user-a", "email": "alice.ngugi@example.com", "claims": {}})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Alice")
        self.assertNotIn("session_service", inspect.getsource(dashboard))

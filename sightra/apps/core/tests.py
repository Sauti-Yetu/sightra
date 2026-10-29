from unittest.mock import MagicMock, patch

from django.test import Client, SimpleTestCase, TestCase

from apps.core.services import GeminiAnalyzer


class LandingAndManifestTests(TestCase):
    def test_landing_focuses_on_vision_and_reader(self):
        client = Client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Reader for text, documents, signs, and currency")
        self.assertContains(res, "app-icon-192.png")
        self.assertContains(res, "sightra-logo.png")

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

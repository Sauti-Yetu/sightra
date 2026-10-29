from django.test import Client, TestCase


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

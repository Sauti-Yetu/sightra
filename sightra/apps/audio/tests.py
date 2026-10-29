from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase

from apps.audio.elevenlabs import voice_id_for


class SpeakApiTests(TestCase):
    def test_missing_text(self):
        client = Client()
        res = client.post("/api/audio/speak/", data={"gender": "female"}, content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_json(self):
        client = Client()
        res = client.post("/api/audio/speak/", data="nope", content_type="application/json")
        self.assertEqual(res.status_code, 400)

    @patch("apps.audio.views.synthesize", return_value=(b"", "audio/mpeg"))
    def test_cloud_voice_unavailable(self, _synth):
        client = Client()
        res = client.post(
            "/api/audio/speak/",
            data={"text": "Hello", "gender": "male"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 503)
        self.assertTrue(res.json()["fallback"])

    @patch("apps.audio.views.synthesize", return_value=(b"ID3fakeaudio", "audio/mpeg"))
    def test_returns_audio(self, _synth):
        client = Client()
        res = client.post(
            "/api/audio/speak/",
            data={"text": "Hello", "gender": "female"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "audio/mpeg")
        self.assertEqual(res.content, b"ID3fakeaudio")


class ElevenLabsVoiceTests(SimpleTestCase):
    def test_voice_ids(self):
        self.assertEqual(voice_id_for("female"), "EXAVITQu4vr4xnSDxMaL")
        self.assertEqual(voice_id_for("male"), "pNInz6obpgDQGcFmaJgB")
        self.assertEqual(voice_id_for("unknown"), "EXAVITQu4vr4xnSDxMaL")

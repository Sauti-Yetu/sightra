from unittest.mock import patch

from django.test import Client, TestCase

from apps.privacy.constants import (
    CONSENT_CAMERA_FEATURE,
    CONSENT_CORE_SERVICE,
    CONSENT_PRIVACY_NOTICE,
    DECISION_GRANTED,
    POLICY_VERSION,
)
from apps.privacy.services.consent_service import SESSION_PRIVACY_KEY


def _grant_camera(client: Client) -> None:
    session = client.session
    session[SESSION_PRIVACY_KEY] = {
        CONSENT_PRIVACY_NOTICE: {"decision": DECISION_GRANTED, "policy_version": POLICY_VERSION},
        CONSENT_CORE_SERVICE: {"decision": DECISION_GRANTED, "policy_version": POLICY_VERSION},
        CONSENT_CAMERA_FEATURE: {"decision": DECISION_GRANTED, "policy_version": POLICY_VERSION},
    }
    session.save()


class NavigationStreamTests(TestCase):
    def test_stream_requires_frame(self):
        client = Client()
        _grant_camera(client)
        res = client.post(
            "/api/navigation/stream/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_stream_requires_consent(self):
        client = Client()
        res = client.post(
            "/api/navigation/stream/",
            data={"frame_data": "data:image/jpeg;base64,aaaa"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "consent_required")

    @patch(
        "apps.navigation.views.analyze_frame_context",
        return_value={
            "analysis_text": "Person near ahead.",
            "vision_metadata": {"objects": [{"label": "person", "box": [1, 2, 3, 4]}], "detector_ready": True},
            "warnings": [],
            "hazard_alert": None,
            "narration_mode": "full",
        },
    )
    def test_stream_returns_analysis_without_csrf(self, _analyze):
        client = Client(enforce_csrf_checks=True)
        _grant_camera(client)
        res = client.post(
            "/api/navigation/stream/",
            data={
                "frame_data": "data:image/jpeg;base64,aaaa",
                "narration_mode": "full",
                "force_refresh": True,
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["analysis_text"], "Person near ahead.")
        self.assertEqual(body["metadata"]["objects"][0]["label"], "person")
        self.assertIsNone(body["audio_url"])

    @patch("apps.core.tasks.process_frame_vision_pipeline")
    @patch("apps.core.tasks.analyzer.analyze_scene", return_value="A doorway is ahead.")
    def test_empty_yolo_still_uses_gemini(self, analyze_scene, pipeline):
        pipeline.return_value = {
            "objects": [],
            "warnings": [],
            "hazard_alert": None,
            "detector_ready": False,
        }
        client = Client()
        _grant_camera(client)
        res = client.post(
            "/api/navigation/stream/",
            data={
                "frame_data": "data:image/jpeg;base64,aaaa",
                "narration_mode": "full",
                "force_refresh": True,
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["analysis_text"], "A doorway is ahead.")
        self.assertTrue(analyze_scene.called)
        self.assertIn("image", analyze_scene.call_args.kwargs)

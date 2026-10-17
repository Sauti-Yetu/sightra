from django.test import Client, TestCase

from apps.privacy.constants import CONSENT_CORE_SERVICE, CONSENT_PRIVACY_NOTICE, DECISION_GRANTED
from apps.privacy.services.consent_service import consent_status_payload, has_core_service_consent


class ConsentServiceTests(TestCase):
    def test_onboarding_required_initially(self):
        client = Client()
        res = client.get("/api/privacy/status/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["requires_onboarding"])

    def test_record_consent_via_api(self):
        client = Client()
        res = client.post(
            "/api/privacy/onboarding/",
            data={
                "privacy_notice_ack": True,
                "core_service_accept": True,
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        status = client.get("/api/privacy/status/").json()
        self.assertFalse(status["requires_onboarding"])
        self.assertEqual(status["decisions"][CONSENT_PRIVACY_NOTICE], DECISION_GRANTED)
        self.assertEqual(status["decisions"][CONSENT_CORE_SERVICE], DECISION_GRANTED)

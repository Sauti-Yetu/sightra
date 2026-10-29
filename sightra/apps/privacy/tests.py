from unittest.mock import patch

from django.db.utils import OperationalError
from django.test import Client, TestCase

from apps.privacy.constants import CONSENT_CORE_SERVICE, CONSENT_PRIVACY_NOTICE, DECISION_GRANTED
from apps.privacy.models import PrivacyProfile
from apps.privacy.models import DataRequest, EmailPreference
from apps.privacy.content.policies import get_all_policies, get_policy


class ConsentServiceTests(TestCase):
    def test_onboarding_required_initially(self):
        client = Client()
        res = client.get("/api/privacy/status/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["requires_onboarding"])
        self.assertTrue(data["requires_cookie_banner"])

    def test_onboarding_requires_age_or_parental(self):
        client = Client()
        res = client.post(
            "/api/privacy/onboarding/",
            data={"privacy_notice_ack": True, "core_service_accept": True},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_record_consent_via_api(self):
        client = Client()
        res = client.post(
            "/api/privacy/onboarding/",
            data={
                "privacy_notice_ack": True,
                "core_service_accept": True,
                "age_adult": True,
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        status = client.get("/api/privacy/status/").json()
        self.assertFalse(status["requires_onboarding"])
        self.assertEqual(status["decisions"][CONSENT_PRIVACY_NOTICE], DECISION_GRANTED)
        self.assertEqual(status["decisions"][CONSENT_CORE_SERVICE], DECISION_GRANTED)

    @patch.object(PrivacyProfile.objects, "get", side_effect=OperationalError("no such column"))
    def test_status_survives_missing_profile_column(self, _get):
        client = Client()
        res = client.get("/api/privacy/status/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("decisions", res.json())


class LegalPagesTests(TestCase):
    def test_canonical_policies_render(self):
        client = Client()
        for slug in get_all_policies():
            res = client.get(f"/legal/{slug}/")
            self.assertEqual(res.status_code, 200, slug)
            self.assertContains(res, get_policy(slug)["title"].split("&")[0].strip())

    def test_legacy_aliases(self):
        client = Client()
        self.assertEqual(client.get("/legal/terms-of-use/").status_code, 200)
        self.assertEqual(client.get("/legal/cookie-storage/").status_code, 200)

    def test_business_and_forms(self):
        client = Client()
        self.assertEqual(client.get("/legal/business/").status_code, 200)
        self.assertContains(client.get("/legal/business/"), "Sauti Yetu")
        self.assertEqual(client.get("/legal/unsubscribe/").status_code, 200)
        self.assertEqual(client.get("/legal/parental-consent/").status_code, 200)
        self.assertEqual(client.get("/legal/rights/").status_code, 200)


class DataRequestTests(TestCase):
    def test_guest_deletion_request(self):
        client = Client()
        res = client.post(
            "/legal/rights/",
            {"kind": "deletion", "email": "person@example.com", "details": "Please delete"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(DataRequest.objects.filter(email="person@example.com", kind="deletion").exists())

    def test_unsubscribe(self):
        client = Client()
        res = client.post("/legal/unsubscribe/", {"email": "person@example.com"})
        self.assertEqual(res.status_code, 200)
        pref = EmailPreference.objects.get(email="person@example.com")
        self.assertFalse(pref.marketing_opt_in)

    def test_cookie_choice(self):
        client = Client()
        res = client.post("/api/privacy/cookies/", data={"optional": False}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        status = client.get("/api/privacy/status/").json()
        self.assertFalse(status["requires_cookie_banner"])
        self.assertEqual(status["decisions"]["optional_cookies"], "denied")


class SignupConsentTests(TestCase):
    def test_signup_rejects_without_terms(self):
        client = Client()
        res = client.post("/signup/", {"email": "a@b.com", "password": "password12", "age_adult": "on"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Please agree to the Terms of Service")

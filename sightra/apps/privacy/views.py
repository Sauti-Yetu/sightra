import json
import logging

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

logger = logging.getLogger(__name__)

from apps.accounts.models import UserPreference
from apps.accounts.services import supabase_client
from apps.privacy.constants import (
    CONSENT_AI_TRAINING,
    CONSENT_ANALYTICS,
    CONSENT_CAMERA_FEATURE,
    CONSENT_CORE_SERVICE,
    CONSENT_LOCATION_FEATURE,
    CONSENT_MICROPHONE_FEATURE,
    CONSENT_OPTIONAL_HISTORY,
    CONSENT_PRIVACY_NOTICE,
    CONSENT_RESEARCH_FEEDBACK,
    DECISION_DENIED,
    DECISION_GRANTED,
    DECISION_WITHDRAWN,
    OPTIONAL_CONSENTS,
    POLICY_VERSION,
)
from apps.privacy.content.policies import get_all_policies, get_policy
from apps.privacy.models import ConsentRecord, PrivacyProfile
from apps.privacy.services.consent_service import (
    consent_status_payload,
    delete_user_privacy_data,
    record_consent,
)


def legal_index(request):
    policies = get_all_policies()
    return render(
        request,
        "legal/index.html",
        {"policies": policies, "policy_version": POLICY_VERSION},
    )


def legal_document(request, slug: str):
    doc = get_policy(slug)
    if not doc:
        raise Http404
    return render(request, "legal/document.html", {"doc": doc, "policy_version": POLICY_VERSION})


def privacy_rights(request):
    return render(request, "legal/rights.html", {"policy_version": POLICY_VERSION})


def privacy_settings(request):
    return render(
        request,
        "legal/privacy_settings.html",
        {
            "policy_version": POLICY_VERSION,
            "status": consent_status_payload(request),
        },
    )


@ensure_csrf_cookie
@require_GET
def api_consent_status(request):
    return JsonResponse(consent_status_payload(request))


@csrf_exempt
@require_POST
def api_consent_update(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    category = (payload.get("category") or "").strip()
    decision = (payload.get("decision") or "").strip()
    if decision not in (DECISION_GRANTED, DECISION_DENIED, DECISION_WITHDRAWN):
        return JsonResponse({"success": False, "error": "Invalid decision"}, status=400)

    allowed = {
        CONSENT_PRIVACY_NOTICE,
        CONSENT_CORE_SERVICE,
        CONSENT_CAMERA_FEATURE,
        CONSENT_MICROPHONE_FEATURE,
        CONSENT_LOCATION_FEATURE,
        CONSENT_OPTIONAL_HISTORY,
        CONSENT_RESEARCH_FEEDBACK,
        CONSENT_AI_TRAINING,
        CONSENT_ANALYTICS,
    }
    if category not in allowed:
        return JsonResponse({"success": False, "error": "Unknown category"}, status=400)

    if category in OPTIONAL_CONSENTS and decision == DECISION_GRANTED:
        if not consent_status_payload(request)["decisions"].get(CONSENT_PRIVACY_NOTICE):
            if payload.get("privacy_notice_ack") is not True:
                pass  # optional consents still require notice ack via onboarding flow

    try:
        if not request.session.session_key:
            request.session.create()
        record = record_consent(
            request,
            category=category,
            decision=decision,
            policy_slug=payload.get("policy_slug") or "",
            purpose=payload.get("purpose") or "",
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )
        request.session.save()
        return JsonResponse({"success": True, "record_id": record.id, "status": consent_status_payload(request)})
    except Exception:
        logger.exception("Consent update failed")
        return JsonResponse({"success": False, "error": "Could not save consent."}, status=500)


@csrf_exempt
@require_POST
def api_onboarding_complete(request):
    """Batch ack for privacy notice + core service after explicit user action."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    if not payload.get("privacy_notice_ack"):
        return JsonResponse({"success": False, "error": "Privacy notice acknowledgement required"}, status=400)
    if not payload.get("core_service_accept"):
        return JsonResponse({"success": False, "error": "Core service acceptance required"}, status=400)

    try:
        if not request.session.session_key:
            request.session.create()

        record_consent(
            request,
            category=CONSENT_PRIVACY_NOTICE,
            decision=DECISION_GRANTED,
            policy_slug="privacy-policy",
            purpose="Shown privacy policy and terms information",
        )
        record_consent(
            request,
            category=CONSENT_CORE_SERVICE,
            decision=DECISION_GRANTED,
            policy_slug="privacy-policy",
            purpose="Provide requested assistive features",
        )

        for opt_key, category in (
            ("optional_history", CONSENT_OPTIONAL_HISTORY),
            ("research_feedback", CONSENT_RESEARCH_FEEDBACK),
            ("ai_training", CONSENT_AI_TRAINING),
            ("analytics", CONSENT_ANALYTICS),
        ):
            if payload.get(opt_key) is True:
                record_consent(
                    request,
                    category=category,
                    decision=DECISION_GRANTED,
                    policy_slug="privacy-policy",
                )
            else:
                record_consent(
                    request,
                    category=category,
                    decision=DECISION_DENIED,
                    policy_slug="privacy-policy",
                )

        request.session.save()
        return JsonResponse({"success": True, "status": consent_status_payload(request)})
    except Exception:
        logger.exception("Privacy onboarding failed")
        return JsonResponse(
            {
                "success": False,
                "error": "Could not save privacy choices on the server. Ensure database migrations have been applied.",
            },
            status=500,
        )


@require_http_methods(["GET", "POST"])
def api_data_export(request):
    user = getattr(request, "sightra_user", None)
    if not user:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    uid = user["id"]
    pref = UserPreference.objects.filter(supabase_user_id=uid).first()
    profile = PrivacyProfile.objects.filter(supabase_user_id=uid).first()
    records = list(
        ConsentRecord.objects.filter(supabase_user_id=uid).values(
            "category", "decision", "policy_version", "created_at", "purpose"
        )[:500]
    )
    export = {
        "user_id": uid,
        "email": user.get("email"),
        "preferences": {
            "theme": pref.theme if pref else None,
            "accessibility": pref.accessibility_json if pref else {},
        },
        "privacy_profile": {
            "privacy_notice_version": profile.privacy_notice_version if profile else None,
            "optional_interaction_history": profile.optional_interaction_history if profile else False,
            "research_product_improvement": profile.research_product_improvement if profile else False,
        },
        "consent_records": records,
        "policy_version": POLICY_VERSION,
    }
    return JsonResponse({"success": True, "export": export})


@require_POST
def api_delete_account_data(request):
    user = getattr(request, "sightra_user", None)
    if not user:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    uid = user["id"]
    UserPreference.objects.filter(supabase_user_id=uid).delete()
    delete_user_privacy_data(uid)

    supabase_deleted = False
    supabase_message = ""
    secret = __import__("os").environ.get("SUPABASE_SECRET_KEY") or ""
    if secret:
        result = supabase_client.admin_delete_user(uid)
        supabase_deleted = result.get("success") is True
        supabase_message = result.get("message") or result.get("error") or ""
    else:
        supabase_message = (
            "Local Sightra data deleted. Supabase account deletion requires server configuration "
            "or manual deletion via Supabase dashboard."
        )

    from apps.accounts.services.session_service import SessionService

    SessionService.clear(request)
    return JsonResponse(
        {
            "success": True,
            "supabase_account_deleted": supabase_deleted,
            "message": supabase_message,
        }
    )

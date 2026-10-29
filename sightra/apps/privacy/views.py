import json
import logging

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

logger = logging.getLogger(__name__)

from apps.accounts.models import UserPreference
from apps.accounts.services import supabase_client
from apps.privacy import legal_config as lc
from apps.privacy.constants import (
    CONSENT_AGE_ADULT,
    CONSENT_AI_TRAINING,
    CONSENT_ANALYTICS,
    CONSENT_CAMERA_FEATURE,
    CONSENT_COOKIES_OPTIONAL,
    CONSENT_CORE_SERVICE,
    CONSENT_LOCATION_FEATURE,
    CONSENT_MARKETING_EMAIL,
    CONSENT_MICROPHONE_FEATURE,
    CONSENT_OPTIONAL_HISTORY,
    CONSENT_PARENTAL,
    CONSENT_PRIVACY_NOTICE,
    CONSENT_RESEARCH_FEEDBACK,
    DECISION_DENIED,
    DECISION_GRANTED,
    DECISION_WITHDRAWN,
    OPTIONAL_CONSENTS,
    POLICY_ALIASES,
    POLICY_VERSION,
)
from apps.privacy.content.policies import get_all_policies, get_policy
from apps.privacy.models import ConsentRecord, DataRequest, PrivacyProfile
from apps.privacy.services.consent_service import (
    consent_status_payload,
    delete_user_privacy_data,
    record_consent,
    set_cookie_choice,
    set_marketing_preference,
)
from apps.privacy.services.data_requests import create_data_request


def legal_index(request):
    policies = get_all_policies()
    return render(
        request,
        "legal/index.html",
        {"policies": policies, "policy_version": POLICY_VERSION},
    )


def legal_document(request, slug: str):
    canonical = POLICY_ALIASES.get(slug, slug)
    doc = get_policy(canonical)
    if not doc:
        raise Http404
    return render(request, "legal/document.html", {"doc": doc, "policy_version": POLICY_VERSION})


def business_details(request):
    return render(
        request,
        "legal/business.html",
        {"org": lc.business_lines(), "policy_version": POLICY_VERSION},
    )


def privacy_rights(request):
    form_message = ""
    form_error = ""
    if request.method == "POST":
        kind = (request.POST.get("kind") or DataRequest.KIND_DELETION).strip()
        email = (request.POST.get("email") or "").strip()
        details = (request.POST.get("details") or "").strip()
        guardian = (request.POST.get("guardian_email") or "").strip()
        user = getattr(request, "sightra_user", None)
        if user and not email:
            email = user.get("email") or ""
        try:
            create_data_request(
                kind=kind,
                email=email,
                details=details,
                guardian_email=guardian,
                supabase_user_id=(user or {}).get("id") or "",
            )
            form_message = (
                "Request received. We will handle deletion, access, or correction using the email you gave. "
                f"If you need a faster response, write to {lc.CONTACT_EMAIL}."
            )
        except ValueError as exc:
            form_error = str(exc)
    return render(
        request,
        "legal/rights.html",
        {
            "policy_version": POLICY_VERSION,
            "form_message": form_message,
            "form_error": form_error,
            "org": lc.business_lines(),
        },
    )


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
    try:
        return JsonResponse(consent_status_payload(request))
    except Exception:
        logger.exception("Consent status failed")
        return JsonResponse(
            {
                "policy_version": POLICY_VERSION,
                "authenticated": bool(getattr(request, "sightra_user", None)),
                "decisions": {},
                "requires_onboarding": False,
                "requires_cookie_banner": False,
            }
        )


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
        CONSENT_COOKIES_OPTIONAL,
        CONSENT_MARKETING_EMAIL,
        CONSENT_AGE_ADULT,
        CONSENT_PARENTAL,
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
    if not payload.get("age_adult") and not payload.get("parental_consent"):
        return JsonResponse(
            {"success": False, "error": "Confirm you are an adult or that a parent/guardian consents."},
            status=400,
        )
    if payload.get("parental_consent") and not payload.get("age_adult"):
        guardian = (payload.get("guardian_email") or "").strip()
        if not guardian or "@" not in guardian:
            return JsonResponse({"success": False, "error": "Guardian email is required for under-18 use."}, status=400)

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
            ("marketing_email", CONSENT_MARKETING_EMAIL),
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

        if payload.get("age_adult"):
            record_consent(
                request,
                category=CONSENT_AGE_ADULT,
                decision=DECISION_GRANTED,
                policy_slug="privacy-policy",
                purpose="User attested they are an adult",
            )
        elif payload.get("parental_consent"):
            record_consent(
                request,
                category=CONSENT_PARENTAL,
                decision=DECISION_GRANTED,
                policy_slug="privacy-policy",
                purpose="Parent or guardian consent attested",
                metadata={"guardian_email": payload.get("guardian_email") or ""},
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


@csrf_exempt
@require_POST
def api_cookie_choice(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    optional = payload.get("optional") is True
    try:
        if not request.session.session_key:
            request.session.create()
        set_cookie_choice(request, optional_accepted=optional)
        request.session.save()
        return JsonResponse({"success": True, "status": consent_status_payload(request)})
    except Exception:
        logger.exception("Cookie choice failed")
        return JsonResponse({"success": False, "error": "Could not save cookie choice."}, status=500)


def unsubscribe(request):
    email = (request.GET.get("email") or request.POST.get("email") or "").strip()
    message = ""
    error = ""
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        if "@" not in email:
            error = "A valid email is required"
            return render(
                request,
                "legal/unsubscribe.html",
                {
                    "email": email,
                    "message": message,
                    "error": error,
                    "org": lc.business_lines(),
                    "policy_version": POLICY_VERSION,
                },
            )
        try:
            pref = set_marketing_preference(email, opt_in=False)
            create_data_request(
                kind=DataRequest.KIND_UNSUBSCRIBE,
                email=pref.email,
                details="Unsubscribe form",
                supabase_user_id=(getattr(request, "sightra_user", None) or {}).get("id") or "",
            )
            if getattr(request, "sightra_user", None):
                record_consent(
                    request,
                    category=CONSENT_MARKETING_EMAIL,
                    decision=DECISION_WITHDRAWN,
                    policy_slug="privacy-policy",
                    purpose="Unsubscribe form",
                )
            message = f"{pref.email} is unsubscribed from optional Sightra emails. Transactional security emails may still be sent by our authentication provider."
        except ValueError as exc:
            error = str(exc)
        except Exception:
            logger.exception("Unsubscribe failed")
            error = "Could not save unsubscribe request. Email us instead."
    return render(
        request,
        "legal/unsubscribe.html",
        {
            "email": email,
            "message": message,
            "error": error,
            "org": lc.business_lines(),
            "policy_version": POLICY_VERSION,
        },
    )


def parental_consent(request):
    message = ""
    error = ""
    if request.method == "POST":
        guardian = (request.POST.get("guardian_email") or "").strip()
        child_email = (request.POST.get("child_email") or "").strip()
        grant = request.POST.get("grant") == "yes"
        details = (request.POST.get("details") or "").strip()
        try:
            create_data_request(
                kind=DataRequest.KIND_PARENTAL,
                email=child_email or guardian,
                guardian_email=guardian,
                details=("Granted. " if grant else "Withdrawn. ") + details,
                supabase_user_id=(getattr(request, "sightra_user", None) or {}).get("id") or "",
            )
            if getattr(request, "sightra_user", None) and grant:
                record_consent(
                    request,
                    category=CONSENT_PARENTAL,
                    decision=DECISION_GRANTED,
                    policy_slug="privacy-policy",
                    purpose="Parental consent form",
                    metadata={"guardian_email": guardian},
                )
            message = "Parental consent request saved. We will contact the guardian email if we need to verify it."
        except ValueError as exc:
            error = str(exc)
    return render(
        request,
        "legal/parental_consent.html",
        {
            "message": message,
            "error": error,
            "org": lc.business_lines(),
            "policy_version": POLICY_VERSION,
            "minimum_age": lc.MINIMUM_AGE,
        },
    )

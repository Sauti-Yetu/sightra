import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.privacy.constants import (
    CONSENT_AGE_ADULT,
    CONSENT_CORE_SERVICE,
    CONSENT_MARKETING_EMAIL,
    CONSENT_PARENTAL,
    CONSENT_PRIVACY_NOTICE,
    DECISION_DENIED,
    DECISION_GRANTED,
)
from apps.privacy.services.consent_service import record_consent, set_marketing_preference
from apps.privacy.services.data_requests import create_data_request

from .auth_messages import auth_error_message, signup_success_message
from .models import UserPreference
from .oauth import build_google_authorize_url
from .services import supabase_client
from .services.session_service import SessionService


def signin(request):
    if getattr(request, "sightra_user", None):
        return redirect(request.GET.get("next") or "/dashboard")
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        result = supabase_client.sign_in_with_password(email, password)
        if result.get("access_token"):
            SessionService.set_from_auth_response(request, result)
            next_url = request.GET.get("next") or request.POST.get("next") or "/dashboard"
            return redirect(next_url)
        messages.error(request, auth_error_message(result))
    return render(request, "signin.html", {"next": request.GET.get("next", "")})


def signup(request):
    if getattr(request, "sightra_user", None):
        return redirect("/dashboard")
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        if request.POST.get("agree_terms") != "on":
            messages.error(request, "Please agree to the Terms of Service to create an account.")
            return render(request, "signup.html")
        if request.POST.get("agree_privacy") != "on":
            messages.error(request, "Please agree to the Privacy Policy to create an account.")
            return render(request, "signup.html")
        age_adult = request.POST.get("age_adult") == "on"
        parental = request.POST.get("parental_consent") == "on"
        guardian_email = (request.POST.get("guardian_email") or "").strip()
        if not age_adult and not parental:
            messages.error(
                request,
                "Confirm you are 18 or older, or that a parent/guardian consents to this account.",
            )
            return render(request, "signup.html")
        if parental and not age_adult and ("@" not in guardian_email):
            messages.error(request, "Enter a parent or guardian email for accounts used by people under 18.")
            return render(request, "signup.html")
        result = supabase_client.sign_up(email, password)
        created = bool(result.get("access_token") or (result.get("user") or {}).get("id") or signup_success_message(result))
        if created:
            if not request.session.session_key:
                request.session.create()
            if result.get("access_token"):
                SessionService.set_from_auth_response(request, result)
            record_consent(
                request,
                category=CONSENT_PRIVACY_NOTICE,
                decision=DECISION_GRANTED,
                policy_slug="privacy-policy",
                purpose="Signup form acknowledgement",
            )
            record_consent(
                request,
                category=CONSENT_CORE_SERVICE,
                decision=DECISION_GRANTED,
                policy_slug="terms-of-service",
                purpose="Signup form acknowledgement",
            )
            if age_adult:
                record_consent(
                    request,
                    category=CONSENT_AGE_ADULT,
                    decision=DECISION_GRANTED,
                    policy_slug="privacy-policy",
                    purpose="Adult age attestation at signup",
                )
            if parental:
                record_consent(
                    request,
                    category=CONSENT_PARENTAL,
                    decision=DECISION_GRANTED,
                    policy_slug="privacy-policy",
                    purpose="Parental consent attestation at signup",
                    metadata={"guardian_email": guardian_email},
                )
                try:
                    create_data_request(
                        kind="parental_consent",
                        email=email,
                        guardian_email=guardian_email,
                        details="Recorded at signup",
                    )
                except ValueError:
                    pass
            marketing = request.POST.get("marketing_email") == "on"
            if email:
                set_marketing_preference(email, opt_in=marketing)
            record_consent(
                request,
                category=CONSENT_MARKETING_EMAIL,
                decision=DECISION_GRANTED if marketing else DECISION_DENIED,
                policy_slug="privacy-policy",
                purpose="Signup marketing checkbox",
            )
            request.session.save()
            if result.get("access_token"):
                return redirect("/dashboard")
            hint = signup_success_message(result)
            messages.success(request, hint or "Account created. You can sign in now.")
            return redirect("/signin/")
        messages.error(request, auth_error_message(result))
    return render(request, "signup.html")


def signout(request):
    SessionService.clear(request)
    return redirect("/signin/")


def auth_google(request):
    next_url = request.GET.get("next") or "/dashboard"
    url = build_google_authorize_url(request, next_url=next_url)
    if not url:
        messages.error(
            request,
            "Google sign-in is not configured. Add SUPABASE_URL and enable Google in Supabase Authentication.",
        )
        return redirect("/signin/")
    return redirect(url)


def auth_callback(request):
    next_url = request.GET.get("next") or request.session.get("oauth_next") or "/dashboard"
    oauth_error = request.GET.get("error_description") or request.GET.get("error")
    if oauth_error:
        messages.error(request, auth_error_message({"error_description": oauth_error}))
        return redirect("/signin/")

    code = request.GET.get("code")
    verifier = request.session.get("oauth_verifier")
    if code:
        if not verifier:
            messages.error(request, "Google sign-in expired. Try Continue with Google again.")
            return redirect("/signin/")
        result = supabase_client.exchange_auth_code(code, verifier)
        request.session.pop("oauth_verifier", None)
        request.session.pop("oauth_next", None)
        if result.get("access_token"):
            SessionService.set_from_auth_response(request, result)
            return redirect(next_url)
        messages.error(request, auth_error_message(result))
        return redirect("/signin/")

    return render(request, "auth_callback.html", {"next": next_url})


@csrf_exempt
@require_POST
def auth_oauth_session(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    if not payload.get("access_token"):
        return JsonResponse({"success": False, "error": "Missing access token"}, status=400)
    SessionService.set_from_auth_response(request, payload)
    return JsonResponse({"success": True, "redirect": payload.get("redirect") or "/dashboard"})


@require_GET
def auth_me(request):
    user = getattr(request, "sightra_user", None) or SessionService.get_user(request)
    if not user:
        return JsonResponse({"authenticated": False})
    return JsonResponse({"authenticated": True, "user": {"id": user["id"], "email": user.get("email")}})


@csrf_exempt
@require_POST
def auth_signin_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    result = supabase_client.sign_in_with_password(
        (payload.get("email") or "").strip(),
        payload.get("password") or "",
    )
    if not result.get("access_token"):
        return JsonResponse({"success": False, "error": auth_error_message(result)}, status=400)
    SessionService.set_from_auth_response(request, result)
    return JsonResponse({"success": True})


@csrf_exempt
@require_POST
def auth_signup_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    result = supabase_client.sign_up(
        (payload.get("email") or "").strip(),
        payload.get("password") or "",
    )
    if result.get("access_token"):
        SessionService.set_from_auth_response(request, result)
        return JsonResponse({"success": True})
    if result.get("user", {}).get("id") or result.get("id"):
        return JsonResponse(
            {
                "success": True,
                "confirm_email": not bool(result.get("access_token")),
                "message": signup_success_message(result),
            }
        )
    return JsonResponse({"success": False, "error": auth_error_message(result)}, status=400)


@require_POST
def auth_signout_api(request):
    SessionService.clear(request)
    return JsonResponse({"success": True})


@require_http_methods(["GET", "POST"])
def preferences_api(request):
    user = getattr(request, "sightra_user", None)
    if not user:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    pref, _ = UserPreference.objects.get_or_create(
        supabase_user_id=user["id"],
        defaults={"email": user.get("email") or ""},
    )

    if request.method == "GET":
        return JsonResponse(
            {
                "theme": pref.theme,
                "accessibility": pref.accessibility_json or {},
            }
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    if "theme" in payload:
        pref.theme = payload["theme"]
    if "accessibility" in payload and isinstance(payload["accessibility"], dict):
        pref.accessibility_json = payload["accessibility"]
    pref.email = user.get("email") or pref.email
    pref.save()
    return JsonResponse({"success": True})

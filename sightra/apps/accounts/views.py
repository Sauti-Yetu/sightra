import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import UserPreference
from .services import supabase_client
from .services.session_service import SessionService


def _auth_error_message(payload: dict) -> str:
    if payload.get("error_description"):
        return str(payload["error_description"])
    if payload.get("msg"):
        return str(payload["msg"])
    if payload.get("error"):
        err = payload["error"]
        return err if isinstance(err, str) else str(err)
    return "Authentication failed. Please try again."


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
        messages.error(request, _auth_error_message(result))
    return render(request, "signin.html", {"next": request.GET.get("next", "")})


def signup(request):
    if getattr(request, "sightra_user", None):
        return redirect("/dashboard")
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        result = supabase_client.sign_up(email, password)
        if result.get("access_token"):
            SessionService.set_from_auth_response(request, result)
            return redirect("/dashboard")
        if result.get("id") or (result.get("user") and not result.get("error")):
            messages.success(request, "Account created. You can sign in now.")
            return redirect("/signin/")
        messages.error(request, _auth_error_message(result))
    return render(request, "signup.html")


def signout(request):
    SessionService.clear(request)
    return redirect("/signin/")


def auth_google(request):
    redirect_to = request.build_absolute_uri(reverse("auth-callback"))
    url = supabase_client.oauth_authorize_url("google", redirect_to)
    if not url:
        messages.error(request, "Google sign-in is not configured.")
        return redirect("/signin/")
    return redirect(url)


def auth_callback(request):
    return render(request, "auth_callback.html", {"next": request.GET.get("next", "/dashboard")})


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
        return JsonResponse({"success": False, "error": _auth_error_message(result)}, status=400)
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
    if result.get("id"):
        return JsonResponse({"success": True, "confirm_email": True})
    return JsonResponse({"success": False, "error": _auth_error_message(result)}, status=400)


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

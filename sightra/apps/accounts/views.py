from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST

from .models import LocalActivityEvent, LocalUserProfile
from .services.session_service import clear_auth_session, log_activity, persist_auth_session
from .services.supabase_client import SupabaseClient, SupabaseError


def _safe_next_url(request) -> str:
    nxt = request.GET.get("next") or request.POST.get("next")
    if nxt and nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return reverse("dashboard")


@require_http_methods(["GET", "POST"])
def signin(request):
    if getattr(request, "supabase_user", None):
        return redirect(_safe_next_url(request))

    error = None
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        client = SupabaseClient()

        if not client.configured:
            error = "Authentication is temporarily unavailable. Please try again later."
        elif not email or not password:
            error = "Email and password are required."
        else:
            try:
                data = client.sign_in_password(email, password)
                persist_auth_session(request, data)
                _mirror_local_profile(data, email)
                LocalActivityEvent.objects.create(
                    supabase_user_id=data.get("user", {}).get("id"),
                    event_type="sign_in",
                    path="/signin/",
                    metadata={"email": email},
                )
                messages.success(request, "Signed in successfully.")
                return redirect(_safe_next_url(request))
            except SupabaseError as exc:
                error = _friendly_auth_error(exc)

    return render(
        request,
        "signin.html",
        {"error": error, "next": request.GET.get("next", "")},
    )


@require_http_methods(["GET", "POST"])
def signup(request):
    if getattr(request, "supabase_user", None):
        return redirect(reverse("dashboard"))

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        client = SupabaseClient()

        if not client.configured:
            error = "Registration is temporarily unavailable. Please try again later."
        elif not email or not password:
            error = "Email and password are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            try:
                data = client.sign_up(email, password, display_name=name or None)
                user = data.get("user") or data
                if data.get("access_token"):
                    persist_auth_session(request, data, display_name=name or None)
                    _mirror_local_profile(data, email, name)
                    LocalActivityEvent.objects.create(
                        supabase_user_id=user.get("id"),
                        event_type="sign_up",
                        path="/signup/",
                        metadata={"email": email},
                    )
                    messages.success(request, "Account created. Welcome to Sightra.")
                    return redirect(reverse("dashboard"))
                messages.info(
                    request,
                    "Check your email to confirm your account, then sign in.",
                )
                return redirect(reverse("signin"))
            except SupabaseError as exc:
                error = _friendly_auth_error(exc)

    return render(request, "signup.html", {"error": error})


@require_POST
def signout(request):
    user = getattr(request, "supabase_user", None)
    if user:
        LocalActivityEvent.objects.create(
            supabase_user_id=user.get("id"),
            event_type="sign_out",
            path="/signout/",
        )
    clear_auth_session(request)
    messages.success(request, "Signed out.")
    return redirect(reverse("landing_page"))


def _mirror_local_profile(auth_payload: dict, email: str, display_name: str | None = None) -> None:
    user = auth_payload.get("user") or auth_payload
    uid = user.get("id")
    if not uid:
        return
    LocalUserProfile.objects.update_or_create(
        supabase_user_id=uid,
        defaults={
            "email": email,
            "display_name": display_name or user.get("user_metadata", {}).get("display_name", ""),
        },
    )


@require_POST
def update_theme_preference(request):
    user = getattr(request, "supabase_user", None)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    theme = (request.POST.get("theme") or "").strip().lower()
    if theme not in ("light", "dark"):
        return JsonResponse({"error": "Invalid theme"}, status=400)

    client = SupabaseClient()
    if client.configured:
        try:
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc).isoformat()
            client.patch_profile(user["id"], {"theme_preference": theme, "updated_at": now})
        except SupabaseError:
            pass

    LocalUserProfile.objects.filter(supabase_user_id=user["id"]).update(theme_preference=theme)
    log_activity(request, "theme_change", metadata={"theme": theme})

    return JsonResponse({"ok": True, "theme": theme})


def _friendly_auth_error(exc: SupabaseError) -> str:
    msg = str(exc).lower()
    if "invalid login credentials" in msg or "invalid_grant" in msg:
        return "Incorrect email or password."
    if "already registered" in msg or "user already registered" in msg:
        return "An account with this email already exists. Try signing in."
    if "password" in msg and "weak" in msg:
        return "Choose a stronger password (at least 8 characters)."
    if exc.status_code and exc.status_code >= 500:
        return "Authentication service error. Please try again shortly."
    return "Could not complete authentication. Please check your details and try again."

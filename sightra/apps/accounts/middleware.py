from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import quote

from .services.session_service import get_session_user, log_activity, refresh_if_needed, touch_session

PUBLIC_PATHS = {"/", "/offline"}
PUBLIC_PREFIXES = (
    "/signin",
    "/signup",
    "/static/",
    "/sw.js",
    "/manifest.webmanifest",
    "/admin/",
)

PROTECTED_PREFIXES = (
    "/dashboard",
    "/vision",
    "/voice_assistant",
    "/live-map",
    "/sightra-connect",
    "/live-call",
    "/settings",
)


def _normalize_path(path: str) -> str:
    if path != "/" and path.endswith("/"):
        return path.rstrip("/")
    return path or "/"


def is_public_path(path: str) -> bool:
    path = _normalize_path(path)
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix.rstrip("/")) or path == prefix.rstrip("/") for prefix in PUBLIC_PREFIXES)


def is_protected_path(path: str) -> bool:
    path = _normalize_path(path)
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


class SupabaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.supabase_user = None  # type: ignore[attr-defined]

        if request.session.get("supabase_user_id"):
            if refresh_if_needed(request):
                request.supabase_user = get_session_user(request)  # type: ignore[attr-defined]
                touch_session(request)
            else:
                request.session.flush()

        return self.get_response(request)


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method != "GET" or response.status_code >= 400:
            return response
        if not getattr(request, "supabase_user", None):
            return response
        if request.path.startswith("/api/"):
            return response

        import time

        bucket = int(time.time() // 60)
        throttle_key = f"activity_throttle:{request.path}:{bucket}"
        if request.session.get(throttle_key):
            return response
        request.session[throttle_key] = True
        request.session.modified = True

        log_activity(request, "page_view", path=request.path)
        return response


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = _normalize_path(request.path)

        if is_protected_path(path) and not is_public_path(path):
            if not getattr(request, "supabase_user", None):
                signin_url = reverse("signin")
                return redirect(f"{signin_url}?next={quote(request.get_full_path())}")

        return self.get_response(request)

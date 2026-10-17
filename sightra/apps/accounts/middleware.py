import re

from django.conf import settings
from django.shortcuts import redirect

from .services.session_service import SessionService

_PUBLIC_PREFIXES = (
    "/signin",
    "/signup",
    "/signout",
    "/auth/",
    "/static/",
    "/admin/",
    "/sw.js",
    "/manifest.webmanifest",
    "/offline/",
    "/legal/",
    "/api/accounts/auth/",
    "/api/privacy/",
)

_PUBLIC_EXACT = {"/", ""}

_PROTECTED_PREFIXES = (
    "/dashboard",
    "/vision/",
    "/live-map/",
    "/voice_assistant/",
    "/live-call/",
    "/sightra-connect/",
    "/settings/",
)


class SupabaseAuthMiddleware:
    """Attach `request.sightra_user` without touching Django auth users."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.sightra_user = SessionService.get_user(request)
        return self.get_response(request)


class LoginRequiredMiddleware:
    """Require sign-in for app routes; landing and auth stay public."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.force_all = getattr(settings, "SIGHTTRA_REQUIRE_LOGIN", False)

    def __call__(self, request):
        if self._is_public(request.path):
            return self.get_response(request)
        if getattr(request, "sightra_user", None):
            return self.get_response(request)
        if self._is_protected(request.path) or self.force_all:
            return redirect(f"{settings.SIGHTTRA_SIGNIN_URL}?next={request.path}")
        return self.get_response(request)

    def _is_public(self, path: str) -> bool:
        if path in _PUBLIC_EXACT:
            return True
        for prefix in _PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        if re.match(r"^/api/", path) and not path.startswith("/api/accounts/"):
            return True
        return False

    def _is_protected(self, path: str) -> bool:
        if path in ("/dashboard", "/dashboard/"):
            return True
        for prefix in _PROTECTED_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

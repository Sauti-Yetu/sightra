import os
import re

from django.conf import settings
from django.shortcuts import redirect

from .services.session_service import SessionService

_PUBLIC_PREFIXES = (
    "/signin",
    "/signup",
    "/signout",
    "/static/",
    "/admin/",
    "/sw.js",
    "/manifest.webmanifest",
    "/offline/",
    "/api/accounts/auth/",
)

_PUBLIC_EXACT = {"/", ""}


class SupabaseAuthMiddleware:
    """Attach `request.sightra_user` without touching Django auth users."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.sightra_user = SessionService.get_user(request)
        return self.get_response(request)


class LoginRequiredMiddleware:
    """Optional gate when SIGHTTRA_REQUIRE_LOGIN=true."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, "SIGHTTRA_REQUIRE_LOGIN", False)

    def __call__(self, request):
        if not self.enabled or self._is_public(request.path):
            return self.get_response(request)
        if getattr(request, "sightra_user", None):
            return self.get_response(request)
        return redirect(f"{settings.SIGHTTRA_SIGNIN_URL}?next={request.path}")

    def _is_public(self, path: str) -> bool:
        if path in _PUBLIC_EXACT:
            return True
        for prefix in _PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        if re.match(r"^/api/", path) and not path.startswith("/api/accounts/"):
            return True
        return False

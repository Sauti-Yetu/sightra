"""Google OAuth helpers: PKCE, public HTTPS callback URL, and authorize redirect."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets

from django.http import HttpRequest
from django.urls import reverse

from .services import supabase_client

OAUTH_VERIFIER_KEY = "oauth_verifier"
OAUTH_NEXT_KEY = "oauth_next"


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def public_absolute_uri(request: HttpRequest, path: str) -> str:
    configured = (os.getenv("SIGHTTRA_PUBLIC_URL") or "").rstrip("/")
    if configured:
        return f"{configured}{path}"
    uri = request.build_absolute_uri(path)
    proto = request.META.get("HTTP_X_FORWARDED_PROTO") or ""
    if proto.startswith("https") and uri.startswith("http://"):
        uri = "https://" + uri[len("http://") :]
    return uri


def build_google_authorize_url(request: HttpRequest, *, next_url: str = "/dashboard") -> str | None:
    callback = public_absolute_uri(request, reverse("auth-callback"))
    verifier, challenge = pkce_pair()
    request.session[OAUTH_VERIFIER_KEY] = verifier
    request.session[OAUTH_NEXT_KEY] = next_url or "/dashboard"
    request.session.modified = True
    return supabase_client.oauth_authorize_url("google", callback, code_challenge=challenge)

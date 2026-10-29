"""Django session helpers for Supabase tokens."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import jwt
from django.http import HttpRequest

from . import supabase_client
from .supabase_client import _ssl_context

logger = logging.getLogger(__name__)

SESSION_KEY = "sightra_supabase"


def display_name_for(user: dict[str, Any] | None) -> str:
    """First-name style label from metadata or the email local-part. Never returns the full email."""
    if not user:
        return ""
    meta = user.get("user_metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    for key in ("given_name", "full_name", "name", "preferred_username"):
        raw = str(meta.get(key) or "").strip()
        if raw:
            return raw.split()[0]
    email = str(user.get("email") or "").strip()
    local = email.split("@")[0].strip() if email else ""
    if not local:
        return ""
    pretty = local.replace(".", " ").replace("_", " ").replace("-", " ").strip()
    first = pretty.split()[0] if pretty else ""
    return first[:1].upper() + first[1:] if first else ""


def _jwks_url() -> str:
    explicit = (os.getenv("SUPABASE_JWKS_URL") or "").strip()
    if explicit:
        return explicit
    base = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    if base:
        return f"{base}/auth/v1/.well-known/jwks.json"
    return ""


def _decode_token(access_token: str) -> dict[str, Any] | None:
    jwks = _jwks_url()
    if not jwks:
        try:
            return jwt.decode(
                access_token,
                options={"verify_signature": False, "verify_aud": False},
            )
        except jwt.PyJWTError:
            return None
    try:
        jwk_client = jwt.PyJWKClient(jwks, ssl_context=_ssl_context())
        signing_key = jwk_client.get_signing_key_from_jwt(access_token)
        return jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256", "ES256", "HS256"],
            audience="authenticated",
            options={"verify_aud": False},
        )
    except Exception:
        logger.debug("JWT verification failed", exc_info=True)
        return None


class SessionService:
    @staticmethod
    def set_from_auth_response(request: HttpRequest, payload: dict[str, Any]) -> bool:
        access = payload.get("access_token")
        if not access:
            return False
        request.session[SESSION_KEY] = {
            "access_token": access,
            "refresh_token": payload.get("refresh_token"),
            "expires_at": time.time() + int(payload.get("expires_in") or 3600),
            "user": payload.get("user") or {},
        }
        request.session.modified = True
        return True

    @staticmethod
    def clear(request: HttpRequest) -> None:
        request.session.pop(SESSION_KEY, None)
        request.session.modified = True

    @staticmethod
    def get_bundle(request: HttpRequest) -> dict[str, Any] | None:
        return request.session.get(SESSION_KEY)

    @staticmethod
    def get_user(request: HttpRequest) -> dict[str, Any] | None:
        bundle = SessionService.get_bundle(request)
        if not bundle:
            return None
        access = bundle.get("access_token")
        if not access:
            return None
        if bundle.get("expires_at", 0) < time.time() + 60:
            refreshed = supabase_client.refresh_session(bundle.get("refresh_token") or "")
            if refreshed.get("access_token"):
                SessionService.set_from_auth_response(request, refreshed)
                bundle = request.session.get(SESSION_KEY) or bundle
                access = bundle.get("access_token")
            else:
                SessionService.clear(request)
                return None
        claims = _decode_token(access or "")
        if not claims:
            return None
        user = bundle.get("user") or {}
        email = user.get("email") or claims.get("email")
        meta = user.get("user_metadata") or user.get("raw_user_meta_data") or {}
        if not isinstance(meta, dict):
            meta = {}
        payload = {
            "id": user.get("id") or claims.get("sub"),
            "email": email,
            "user_metadata": meta,
            "claims": claims,
        }
        payload["display_name"] = display_name_for(payload)
        return payload

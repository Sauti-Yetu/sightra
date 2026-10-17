"""Supabase Auth HTTP client (stdlib only). Isolated from app business logic."""

from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


def _ssl_context() -> ssl.SSLContext:
    """Reliable HTTPS on macOS/Python builds missing system CA bundles."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _settings() -> tuple[str, str]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
    return url, key


def _request(method: str, path: str, payload: dict | None = None) -> dict[str, Any]:
    base, apikey = _settings()
    if not base or not apikey:
        return {"error": "Supabase is not configured on the server."}

    data = None
    headers = {
        "apikey": apikey,
        "Content-Type": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except Exception:
            detail = {"error": exc.reason or "Request failed"}
        detail["_status"] = exc.code
        return detail
    except Exception as exc:
        logger.exception("Supabase request failed")
        return {"error": str(exc)}


def sign_up(email: str, password: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/v1/signup",
        {"email": email, "password": password},
    )


def sign_in_with_password(email: str, password: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/v1/token?grant_type=password",
        {"email": email, "password": password},
    )


def oauth_authorize_url(provider: str, redirect_to: str) -> str | None:
    base, apikey = _settings()
    if not base or not apikey:
        return None
    from urllib.parse import quote

    return (
        f"{base}/auth/v1/authorize?provider={quote(provider)}"
        f"&redirect_to={quote(redirect_to, safe='')}"
        f"&apikey={quote(apikey)}"
    )


def refresh_session(refresh_token: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/v1/token?grant_type=refresh_token",
        {"refresh_token": refresh_token},
    )


def _admin_request(method: str, path: str) -> dict[str, Any]:
    """Service-role calls (e.g. account deletion). Requires SUPABASE_SECRET_KEY."""
    base = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    secret = os.getenv("SUPABASE_SECRET_KEY") or ""
    if not base or not secret:
        return {"success": False, "error": "Supabase admin API is not configured."}

    req = urllib.request.Request(
        f"{base}{path}",
        headers={
            "apikey": secret,
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as resp:
            body = resp.read().decode("utf-8")
            return {"success": True, "message": "Deleted", "body": json.loads(body) if body else {}}
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except Exception:
            detail = {"error": exc.reason or "Request failed"}
        detail["success"] = False
        return detail
    except Exception as exc:
        logger.exception("Supabase admin request failed")
        return {"success": False, "error": str(exc)}


def admin_delete_user(user_id: str) -> dict[str, Any]:
    if not user_id:
        return {"success": False, "error": "Missing user id"}
    return _admin_request("DELETE", f"/auth/v1/admin/users/{user_id}")

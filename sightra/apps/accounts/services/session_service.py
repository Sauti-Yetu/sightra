"""Django session ↔ Supabase auth + tracking session rows."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.http import HttpRequest

from .supabase_client import SupabaseClient, SupabaseError

logger = logging.getLogger(__name__)

SESSION_USER_ID = "supabase_user_id"
SESSION_EMAIL = "supabase_email"
SESSION_ACCESS = "supabase_access_token"
SESSION_REFRESH = "supabase_refresh_token"
SESSION_TRACKING_ID = "supabase_tracking_session_id"
SESSION_DISPLAY_NAME = "supabase_display_name"


def _client() -> SupabaseClient:
    return SupabaseClient()


def persist_auth_session(request: HttpRequest, auth_payload: dict, *, display_name: str | None = None) -> None:
    """Store Supabase tokens and start tracking session."""
    user = auth_payload.get("user") or {}
    user_id = user.get("id") or auth_payload.get("id")
    if not user_id:
        raise SupabaseError("Authentication response did not include a user id.")

    email = user.get("email") or auth_payload.get("email")
    access = auth_payload.get("access_token")
    refresh = auth_payload.get("refresh_token")

    request.session[SESSION_USER_ID] = user_id
    request.session[SESSION_EMAIL] = email
    request.session[SESSION_ACCESS] = access
    request.session[SESSION_REFRESH] = refresh
    if display_name:
        request.session[SESSION_DISPLAY_NAME] = display_name

    request.session.modified = True
    _sync_profile_and_tracking(request, user_id, email, display_name)


def clear_auth_session(request: HttpRequest) -> None:
    access = request.session.get(SESSION_ACCESS)
    tracking_id = request.session.get(SESSION_TRACKING_ID)

    if access:
        try:
            _client().sign_out(access)
        except SupabaseError:
            logger.debug("Remote sign-out failed", exc_info=True)

    if tracking_id:
        try:
            _client().patch_session_row(
                tracking_id,
                {"ended_at": datetime.now(timezone.utc).isoformat()},
            )
        except SupabaseError:
            logger.debug("Failed to close tracking session", exc_info=True)

    for key in (
        SESSION_USER_ID,
        SESSION_EMAIL,
        SESSION_ACCESS,
        SESSION_REFRESH,
        SESSION_TRACKING_ID,
        SESSION_DISPLAY_NAME,
    ):
        request.session.pop(key, None)
    request.session.flush()


def get_session_user(request: HttpRequest) -> dict | None:
    user_id = request.session.get(SESSION_USER_ID)
    if not user_id:
        return None
    return {
        "id": user_id,
        "email": request.session.get(SESSION_EMAIL),
        "display_name": request.session.get(SESSION_DISPLAY_NAME),
    }


def refresh_if_needed(request: HttpRequest) -> bool:
    """Refresh access token using refresh_token. Returns True if session still valid."""
    refresh = request.session.get(SESSION_REFRESH)
    access = request.session.get(SESSION_ACCESS)
    if not refresh:
        return bool(access)

    client = _client()
    try:
        if access:
            client.get_user(access)
            return True
    except SupabaseError:
        pass

    try:
        data = client.refresh_session(refresh)
    except SupabaseError:
        return False

    request.session[SESSION_ACCESS] = data.get("access_token")
    request.session[SESSION_REFRESH] = data.get("refresh_token", refresh)
    request.session.modified = True
    return True


def _sync_profile_and_tracking(
    request: HttpRequest,
    user_id: str,
    email: str | None,
    display_name: str | None,
) -> None:
    client = _client()
    if not client.configured:
        return

    now = datetime.now(timezone.utc).isoformat()
    profile = {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "last_seen_at": now,
        "updated_at": now,
    }
    try:
        client.upsert_profile(profile)
    except SupabaseError:
        logger.warning("Profile upsert failed for user %s", user_id, exc_info=True)

    ua = request.META.get("HTTP_USER_AGENT", "")[:512]
    ip = _client_ip(request)
    device = _device_class(ua)

    row = {
        "user_id": user_id,
        "django_session_key": request.session.session_key,
        "ip_address": ip,
        "user_agent": ua,
        "device_class": device,
        "last_active_at": now,
    }
    try:
        created = client.insert_session_row(row)
        if created and created.get("id"):
            request.session[SESSION_TRACKING_ID] = created["id"]
            request.session.modified = True
    except SupabaseError:
        logger.warning("Tracking session insert failed", exc_info=True)


def touch_session(request: HttpRequest) -> None:
    user = get_session_user(request)
    if not user:
        return
    client = _client()
    if not client.configured:
        return

    now = datetime.now(timezone.utc).isoformat()
    tracking_id = request.session.get(SESSION_TRACKING_ID)
    try:
        client.patch_profile(user["id"], {"last_seen_at": now, "updated_at": now})
        if tracking_id:
            client.patch_session_row(tracking_id, {"last_active_at": now})
    except SupabaseError:
        logger.debug("Session touch failed", exc_info=True)


def log_activity(
    request: HttpRequest,
    event_type: str,
    *,
    path: str | None = None,
    metadata: dict | None = None,
) -> None:
    user = get_session_user(request)
    if not user:
        return
    client = _client()
    if not client.configured:
        return

    row = {
        "user_id": user["id"],
        "session_id": request.session.get(SESSION_TRACKING_ID),
        "event_type": event_type,
        "path": path or request.path,
        "metadata": metadata or {},
    }
    try:
        client.insert_activity_event(row)
    except SupabaseError:
        logger.debug("Activity log failed", exc_info=True)


def _client_ip(request: HttpRequest) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "")[:64]


def _device_class(user_agent: str) -> str:
    ua = user_agent.lower()
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        return "mobile"
    if "tablet" in ua or "ipad" in ua:
        return "tablet"
    return "desktop"

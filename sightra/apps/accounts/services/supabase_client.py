"""Supabase HTTP client for Auth and PostgREST (server-side only)."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class SupabaseError(Exception):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SupabaseClient:
    def __init__(self) -> None:
        self.url = (settings.SUPABASE_URL or "").rstrip("/")
        self.publishable_key = settings.SUPABASE_PUBLISHABLE_KEY
        self.secret_key = settings.SUPABASE_SECRET_KEY

    @property
    def configured(self) -> bool:
        return bool(self.url and self.publishable_key and self.secret_key)

    def _headers(self, *, use_secret: bool = False, user_access_token: str | None = None, extra: dict | None = None) -> dict[str, str]:
        key = self.secret_key if use_secret else self.publishable_key
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {user_access_token or key}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
        use_secret: bool = False,
        user_access_token: str | None = None,
        prefer: str | None = None,
    ) -> Any:
        if not self.configured:
            raise SupabaseError("Supabase is not configured. Set SUPABASE_* environment variables.")

        extra = {"Prefer": prefer} if prefer else None
        headers = self._headers(use_secret=use_secret, user_access_token=user_access_token, extra=extra)
        url = f"{self.url}{path}"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(method, url, headers=headers, json=json, params=params)
        except httpx.HTTPError as exc:
            logger.exception("Supabase request failed: %s %s", method, path)
            raise SupabaseError("Unable to reach Supabase.") from exc

        if response.status_code >= 400:
            try:
                payload = response.json()
                msg = (
                    payload.get("msg")
                    or payload.get("error_description")
                    or payload.get("message")
                    or str(payload)
                )
            except Exception:
                payload = response.text
                msg = response.text or "Supabase request failed."
            raise SupabaseError(str(msg), status_code=response.status_code, payload=payload)

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def sign_up(self, email: str, password: str, display_name: str | None = None) -> dict:
        body: dict[str, Any] = {"email": email, "password": password}
        if display_name:
            body["data"] = {"display_name": display_name}
        return self._request("POST", "/auth/v1/signup", json=body)

    def sign_in_password(self, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )

    def refresh_session(self, refresh_token: str) -> dict:
        return self._request(
            "POST",
            "/auth/v1/token",
            params={"grant_type": "refresh_token"},
            json={"refresh_token": refresh_token},
        )

    def get_user(self, access_token: str) -> dict:
        return self._request("GET", "/auth/v1/user", user_access_token=access_token)

    def sign_out(self, access_token: str) -> None:
        try:
            self._request("POST", "/auth/v1/logout", user_access_token=access_token)
        except SupabaseError:
            pass

    def upsert_profile(self, profile: dict) -> None:
        self._request(
            "POST",
            "/rest/v1/profiles",
            json=profile,
            params={"on_conflict": "id"},
            use_secret=True,
            prefer="resolution=merge-duplicates",
        )

    def patch_profile(self, user_id: str, fields: dict) -> None:
        self._request(
            "PATCH",
            f"/rest/v1/profiles?id=eq.{user_id}",
            json=fields,
            use_secret=True,
        )

    def insert_session_row(self, row: dict) -> dict | None:
        result = self._request(
            "POST",
            "/rest/v1/user_sessions",
            json=row,
            use_secret=True,
            prefer="return=representation",
        )
        if isinstance(result, list) and result:
            return result[0]
        return None

    def patch_session_row(self, session_id: str, fields: dict) -> None:
        self._request(
            "PATCH",
            f"/rest/v1/user_sessions?id=eq.{session_id}",
            json=fields,
            use_secret=True,
        )

    def insert_activity_event(self, row: dict) -> None:
        self._request("POST", "/rest/v1/user_activity_events", json=row, use_secret=True)

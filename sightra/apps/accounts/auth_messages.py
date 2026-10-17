"""Map Supabase Auth API errors to user-safe messages."""

from __future__ import annotations

from typing import Any


def auth_error_message(payload: dict[str, Any]) -> str:
    status = payload.get("_status")
    parts: list[str] = []
    for key in ("msg", "error_description", "message"):
        val = payload.get(key)
        if val:
            parts.append(str(val))
    err = payload.get("error")
    if isinstance(err, str):
        parts.append(err)
    elif isinstance(err, dict):
        for key in ("message", "msg"):
            if err.get(key):
                parts.append(str(err[key]))

    combined = " ".join(parts).lower()

    if status == 429 or "rate limit" in combined or "email rate limit" in combined:
        return (
            "Too many sign-up or sign-in attempts for this email. Wait 15–60 minutes, "
            "or in Supabase Dashboard disable “Confirm email” for testing and check Auth rate limits."
        )
    if "already registered" in combined or "user already exists" in combined:
        return "An account with this email already exists. Sign in instead, or use password recovery in Supabase."
    if "invalid login credentials" in combined or "invalid_grant" in combined:
        return (
            "Incorrect email or password. If you recently signed up, confirm your email first "
            "(Supabase → Authentication → Providers → Email: turn off “Confirm email” for instant access)."
        )
    if "email not confirmed" in combined or "not confirmed" in combined:
        return "Please confirm your email using the link Supabase sent, then sign in again."

    if parts:
        return parts[0]
    return "Authentication failed. Please try again."


def signup_success_message(payload: dict[str, Any]) -> str | None:
    if payload.get("access_token"):
        return None
    user = payload.get("user") or {}
    if user.get("id"):
        return (
            "Account created. If email confirmation is enabled in Supabase, check your inbox, "
            "then sign in. Otherwise try signing in now."
        )
    return None

"""Native Gemini REST client. Auth keys (AQ.) use x-goog-api-key, never logged."""

from __future__ import annotations

import logging

import httpx

from app.utils.errors import NETWORK_FAILURE, UNCLEAR_IMAGE, UserFacingError

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_FALLBACK_MODELS = (
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
)


def generate_content(api_key: str, model: str, body: dict, timeout: float = 25.0) -> dict:
    if not api_key:
        raise UserFacingError(
            "Visual analysis isn't configured yet. Add an AI_API_KEY to enable reading.",
            status_code=503,
        )
    tried: list[str] = []
    last_status = 0
    for candidate in _model_chain(model):
        tried.append(candidate)
        url = f"{GEMINI_BASE}/models/{candidate}:generateContent"
        try:
            response = _post(url, api_key, body, timeout)
        except httpx.TimeoutException:
            logger.warning("Gemini request timed out, trying next model")
            last_status = 504
            continue
        except httpx.HTTPError:
            logger.warning("Gemini request failed, trying next model")
            last_status = 503
            continue
        last_status = response.status_code
        if response.status_code == 404:
            logger.info("Gemini model unavailable, trying next")
            continue
        if response.is_success:
            return response.json()
        raise _error_for_status(response.status_code)
    logger.warning("Gemini models unavailable after %s attempts", len(tried))
    raise _error_for_status(last_status or 503)


def extract_text(payload: dict) -> str:
    candidates = payload.get("candidates") or [{}]
    parts = (candidates[0].get("content") or {}).get("parts") or [{}]
    return str(parts[0].get("text") or "").strip()


def _model_chain(preferred: str) -> list[str]:
    ordered = [preferred] if preferred else []
    for name in GEMINI_FALLBACK_MODELS:
        if name not in ordered:
            ordered.append(name)
    return ordered


def _post(url: str, api_key: str, body: dict, timeout: float) -> httpx.Response:
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    response = httpx.post(url, headers=headers, json=body, timeout=timeout)
    if response.status_code in (401, 403):
        response = httpx.post(url, params={"key": api_key}, json=body, timeout=timeout)
    return response


def _error_for_status(status: int) -> UserFacingError:
    if status in (400, 422):
        return UserFacingError(UNCLEAR_IMAGE, status_code=422)
    return UserFacingError(NETWORK_FAILURE, status_code=503)

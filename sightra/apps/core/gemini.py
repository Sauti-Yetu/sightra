"""Shared Gemini calls with timeouts and model fallbacks."""

from __future__ import annotations

import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Faster flash-lite first; heavier flash is the fallback.
GEMINI_MODELS = (
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite-preview",
)
DEFAULT_TIMEOUT = 8
MAX_MODEL_ATTEMPTS = 2

_configured = False
_working_model: str | None = None


def configure() -> None:
    global _configured
    genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "")
    _configured = True


def _response_text(response) -> str:
    try:
        return (getattr(response, "text", None) or "").strip()
    except Exception:
        parts: list[str] = []
        for cand in getattr(response, "candidates", None) or []:
            content = getattr(cand, "content", None)
            for part in getattr(content, "parts", None) or []:
                text = getattr(part, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()


def _model_order() -> tuple[str, ...]:
    if _working_model and _working_model in GEMINI_MODELS:
        return (_working_model,) + tuple(name for name in GEMINI_MODELS if name != _working_model)
    return GEMINI_MODELS


def generate_text(
    parts: list,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_attempts: int = MAX_MODEL_ATTEMPTS,
    generation_config: dict | None = None,
) -> str:
    """
    Generate text from prompt parts (strings and/or PIL images).
    Raises the last error if every attempted model fails.
    """
    global _working_model
    if not _configured:
        configure()
    last: Exception | None = None
    attempts = max(1, int(max_attempts or MAX_MODEL_ATTEMPTS))
    config = generation_config
    for index, name in enumerate(_model_order()):
        if index >= attempts:
            break
        try:
            model = genai.GenerativeModel(name)
            kwargs = {"request_options": {"timeout": timeout}}
            if config:
                kwargs["generation_config"] = config
            response = model.generate_content(parts, **kwargs)
            text = _response_text(response)
            if text:
                _working_model = name
                return text
        except Exception as exc:
            last = exc
            logger.warning("Gemini model %s failed: %s", name, exc)
    if last:
        raise last
    raise RuntimeError("Gemini returned an empty response.")

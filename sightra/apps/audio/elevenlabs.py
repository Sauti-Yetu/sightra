"""ElevenLabs text-to-speech. Falls back to empty bytes if unconfigured."""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

DEFAULT_FEMALE = "EXAVITQu4vr4xnSDxMaL"  # Sarah
DEFAULT_MALE = "pNInz6obpgDQGcFmaJgB"  # Adam
MODEL_ID = "eleven_multilingual_v2"


def _api_key() -> str:
    return (os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def voice_id_for(gender: str) -> str:
    gender = (gender or "female").lower()
    if gender == "male":
        return (os.environ.get("ELEVENLABS_VOICE_MALE") or DEFAULT_MALE).strip()
    return (os.environ.get("ELEVENLABS_VOICE_FEMALE") or DEFAULT_FEMALE).strip()


def synthesize(text: str, *, gender: str = "female") -> tuple[bytes, str]:
    """
    Return (audio_bytes, content_type). Empty bytes if the key is missing or the API fails.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return b"", "audio/mpeg"
    key = _api_key()
    if not key:
        logger.warning("ELEVENLABS_API_KEY is not set; skipping cloud TTS")
        return b"", "audio/mpeg"

    voice_id = voice_id_for(gender)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    try:
        response = requests.post(
            url,
            headers={
                "xi-api-key": key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json={
                "text": cleaned[:4500],
                "model_id": MODEL_ID,
                "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
            },
            timeout=45,
        )
        if response.status_code >= 400:
            logger.error("ElevenLabs TTS failed: %s %s", response.status_code, response.text[:200])
            return b"", "audio/mpeg"
        return response.content, response.headers.get("Content-Type", "audio/mpeg")
    except Exception:
        logger.exception("ElevenLabs TTS request failed")
        return b"", "audio/mpeg"

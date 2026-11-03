"""Reading-voice catalogue for spoken guidance.

These are the trained ElevenLabs voices Sightra can use today. A future
release will let a user record a preferred voice and store a clone id
under READING_VOICE_CUSTOM. Until then that option stays disabled in UI.
"""

from __future__ import annotations

READING_VOICE_CUSTOM = "custom"

# Public preset voices. Keys are stored in user accessibility prefs as `readingVoice`.
READING_VOICES: dict[str, dict[str, str]] = {
    "sarah": {
        "id": "EXAVITQu4vr4xnSDxMaL",
        "label": "Sarah",
        "gender": "female",
        "description": "Clear, calm reading voice",
    },
    "rachel": {
        "id": "21m00Tcm4TlvDq8ikWAM",
        "label": "Rachel",
        "gender": "female",
        "description": "Warm narrative voice",
    },
    "charlotte": {
        "id": "XB0fDUnXU5powFXDhCwa",
        "label": "Charlotte",
        "gender": "female",
        "description": "Soft, even spoken guidance",
    },
    "adam": {
        "id": "pNInz6obpgDQGcFmaJgB",
        "label": "Adam",
        "gender": "male",
        "description": "Steady, direct reading voice",
    },
    "liam": {
        "id": "TX3LPaxmHKxFdv7VOQHJ",
        "label": "Liam",
        "gender": "male",
        "description": "Bright, conversational voice",
    },
    "brian": {
        "id": "nPczCjzI2devNBz1zQrb",
        "label": "Brian",
        "gender": "male",
        "description": "Lower, measured voice",
    },
}

DEFAULT_READING_VOICE = "sarah"


def resolve_voice(voice_key: str | None = None, gender: str | None = None) -> dict[str, str]:
    """Return a catalogue entry. Unknown keys fall back by gender, then Sarah."""
    key = (voice_key or "").strip().lower()
    if key and key != READING_VOICE_CUSTOM and key in READING_VOICES:
        return READING_VOICES[key]
    if (gender or "").lower() == "male":
        return READING_VOICES["adam"]
    return READING_VOICES[DEFAULT_READING_VOICE]

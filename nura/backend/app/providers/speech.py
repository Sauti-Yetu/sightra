"""ElevenLabs speech provider. API key never leaves the backend."""

from __future__ import annotations

import io
import logging

from app.utils.errors import STT_UNAVAILABLE, TTS_UNAVAILABLE, UserFacingError

logger = logging.getLogger(__name__)


class ElevenLabsSpeechProvider:
    name = "elevenlabs"

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        tts_model_id: str,
        stt_model_id: str = "scribe_v2",
    ) -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.tts_model_id = tts_model_id
        self.stt_model_id = stt_model_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            from elevenlabs import ElevenLabs

            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def synthesize(self, text: str, speed: float = 1.0) -> bytes:
        if not self.api_key:
            raise UserFacingError(TTS_UNAVAILABLE, status_code=503)
        cleaned = (text or "").strip()
        if not cleaned:
            raise UserFacingError(TTS_UNAVAILABLE, status_code=400)
        speed = max(0.7, min(1.2, speed))
        try:
            from elevenlabs.types.voice_settings import VoiceSettings

            client = self._get_client()
            audio = client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id=self.tts_model_id,
                text=cleaned,
                output_format="mp3_44100_128",
                voice_settings=VoiceSettings(
                    stability=0.45,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True,
                    speed=speed,
                ),
            )
            if isinstance(audio, (bytes, bytearray)):
                return bytes(audio)
            chunks = bytearray()
            for chunk in audio:
                if chunk:
                    chunks.extend(chunk)
            return bytes(chunks)
        except UserFacingError:
            raise
        except Exception as exc:
            logger.exception("ElevenLabs TTS failed")
            raise UserFacingError(TTS_UNAVAILABLE, status_code=503) from exc

    def transcribe(self, audio: bytes, mime_type: str = "audio/webm") -> str:
        if not self.api_key:
            raise UserFacingError(STT_UNAVAILABLE, status_code=503)
        if not audio:
            raise UserFacingError(STT_UNAVAILABLE, status_code=400)
        try:
            client = self._get_client()
            buffer = io.BytesIO(audio)
            suffix = _suffix_for(mime_type)
            buffer.name = f"speech{suffix}"
            result = client.speech_to_text.convert(
                file=buffer,
                model_id=self.stt_model_id,
            )
            text = getattr(result, "text", None) or (result.get("text") if isinstance(result, dict) else "")
            return str(text or "").strip()
        except UserFacingError:
            raise
        except Exception as exc:
            logger.exception("ElevenLabs STT failed")
            raise UserFacingError(STT_UNAVAILABLE, status_code=503) from exc


def _suffix_for(mime_type: str) -> str:
    mapping = {
        "audio/webm": ".webm",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".m4a",
        "audio/m4a": ".m4a",
        "audio/ogg": ".ogg",
    }
    return mapping.get(mime_type.split(";")[0].strip().lower(), ".webm")

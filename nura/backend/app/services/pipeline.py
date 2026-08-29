"""Visual analysis pipeline: image → preprocess → vision/OCR → structure → speech."""

from __future__ import annotations

import logging

import httpx

from app.config import Settings
from app.providers.context import MemoryContextProvider
from app.providers.currency import CurrencyService
from app.providers.gemini import extract_text, generate_content
from app.providers.ocr import VisionOCRProvider
from app.providers.prompts import ask_prompt
from app.providers.speech import ElevenLabsSpeechProvider
from app.providers.vision import NullVisionProvider, build_vision_provider, parse_json_object
from app.schemas.common import AnalysisResult, ReadMode, Verbosity
from app.services.image import preprocess_image
from app.services.verbosity import ensure_spoken
from app.utils.errors import (
    EMPTY_RESULT,
    GENERIC,
    LOW_CONFIDENCE,
    NETWORK_FAILURE,
    NO_CONTEXT,
    UserFacingError,
)

logger = logging.getLogger(__name__)


class VisualPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.vision = build_vision_provider(
            settings.ai_provider,
            settings.ai_api_key,
            settings.resolved_ai_model,
        )
        self.ocr = VisionOCRProvider(self.vision)
        self.currency = CurrencyService()
        self.context = MemoryContextProvider(ttl_seconds=settings.session_ttl_seconds)
        self.speech = ElevenLabsSpeechProvider(
            api_key=settings.elevenlabs_api_key,
            voice_id=settings.elevenlabs_voice_id,
            tts_model_id=settings.elevenlabs_model_id,
            stt_model_id=settings.elevenlabs_stt_model_id,
        )

    def analyze(
        self,
        image: bytes,
        mode: ReadMode,
        verbosity: Verbosity,
        session_id: str,
        question: str | None = None,
    ) -> AnalysisResult:
        processed = preprocess_image(image, self.settings.max_image_dimension)
        if isinstance(self.vision, NullVisionProvider):
            raise UserFacingError(
                "Visual analysis isn't configured yet. Add an AI_API_KEY to enable reading.",
                status_code=503,
            )
        try:
            result = self.vision.analyze(processed, mode, verbosity, question)
        except UserFacingError:
            raise
        except Exception as exc:
            logger.exception("Vision analysis failed")
            raise UserFacingError(GENERIC, status_code=500) from exc

        if mode == "currency":
            identified = self.currency.identify_from_analysis(
                denomination=result.currency.denomination if result.currency else None,
                confidence=result.currency.confidence if result.currency else result.confidence,
                verbosity=verbosity,
                ocr_text=result.text,
            )
            from app.schemas.common import CurrencyResult

            result.type = "currency"
            result.currency = CurrencyResult(**identified)
            result.spoken = identified["spoken"]
            result.confidence = identified["confidence"]
            if identified["denomination"] and not result.summary:
                result.summary = identified["spoken"]

        result = ensure_spoken(result, verbosity)
        result = _apply_confidence_language(result)

        if not result.text.strip() and not (result.currency and result.currency.denomination):
            if result.confidence < 0.45:
                raise UserFacingError(EMPTY_RESULT, status_code=422)

        self.context.save_scan(session_id, result)
        return result

    def ask(self, session_id: str, question: str, verbosity: Verbosity) -> dict:
        record = self.context.get(session_id)
        if not record or not record.get("last_scan"):
            raise UserFacingError(NO_CONTEXT, status_code=409)
        import json

        prompt = ask_prompt(question, json.dumps(record["last_scan"]), verbosity)
        answer_text = self._complete_text(prompt)
        try:
            payload = parse_json_object(answer_text)
        except ValueError:
            payload = {"spoken": answer_text, "summary": answer_text, "confidence": 0.7}
        spoken = str(payload.get("spoken") or payload.get("summary") or "").strip()
        if not spoken:
            spoken = "I couldn't find that in the current scan."
        self.context.add_turn(session_id, "user", question)
        self.context.add_turn(session_id, "nura", spoken)
        return {
            "spoken": spoken,
            "summary": str(payload.get("summary") or spoken),
            "confidence": float(payload.get("confidence") or 0.7),
            "last_scan": record["last_scan"],
        }

    def _complete_text(self, prompt: str) -> str:
        if not self.settings.has_ai:
            raise UserFacingError(
                "Visual analysis isn't configured yet. Add an AI_API_KEY to enable reading.",
                status_code=503,
            )
        try:
            if self.settings.ai_provider == "openai":
                response = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.ai_api_key}"},
                    json={
                        "model": self.settings.resolved_ai_model,
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            data = generate_content(
                self.settings.ai_api_key,
                self.settings.resolved_ai_model,
                {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json",
                    },
                },
                timeout=30.0,
            )
            return extract_text(data)
        except UserFacingError:
            raise
        except httpx.HTTPError as exc:
            logger.exception("Ask completion failed")
            raise UserFacingError(NETWORK_FAILURE, status_code=503) from exc


def _apply_confidence_language(result: AnalysisResult) -> AnalysisResult:
    if result.confidence >= 0.45:
        return result
    if result.spoken and "not completely certain" not in result.spoken.lower():
        result.spoken = f"{result.spoken.rstrip('.')} I'm not completely certain."
    elif not result.spoken:
        result.spoken = LOW_CONFIDENCE
    return result

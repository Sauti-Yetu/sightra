"""Multimodal vision providers. Selected by AI_PROVIDER; never leak API keys."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.providers.prompts import analysis_prompt
from app.schemas.common import AnalysisResult, ContentType, DocumentFields, CurrencyResult, ReadMode, Verbosity
from app.utils.errors import NETWORK_FAILURE, UNCLEAR_IMAGE, UserFacingError

logger = logging.getLogger(__name__)

CONTENT_TYPES: set[str] = {
    "text",
    "document",
    "sign",
    "currency",
    "chart",
    "table",
    "screen",
    "label",
    "other",
}


def parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
    raise ValueError("Model did not return JSON")


def result_from_payload(payload: dict[str, Any]) -> AnalysisResult:
    content_type = payload.get("type") if payload.get("type") in CONTENT_TYPES else "text"
    currency_payload = payload.get("currency")
    document_payload = payload.get("document")
    currency = None
    if isinstance(currency_payload, dict) and (
        currency_payload.get("denomination") is not None or currency_payload.get("currency")
    ):
        currency = CurrencyResult(
            currency=str(currency_payload.get("currency") or "KES"),
            denomination=_int_or_none(currency_payload.get("denomination")),
            confidence=_clamp(currency_payload.get("confidence", payload.get("confidence", 0))),
            spoken=str(currency_payload.get("spoken") or payload.get("spoken") or ""),
        )
    document = None
    if isinstance(document_payload, dict):
        document = DocumentFields(
            document_type=_str_or_none(document_payload.get("document_type")),
            audience=_str_or_none(document_payload.get("audience")),
            dates=_str_list(document_payload.get("dates")),
            amounts=_str_list(document_payload.get("amounts")),
            action_required=_str_or_none(document_payload.get("action_required")),
            sections=_str_list(document_payload.get("sections")),
        )
    return AnalysisResult(
        type=content_type,  # type: ignore[arg-type]
        confidence=_clamp(payload.get("confidence", 0)),
        text=str(payload.get("text") or "").strip(),
        title=_str_or_none(payload.get("title")),
        important_information=_str_list(payload.get("important_information")),
        summary=str(payload.get("summary") or "").strip(),
        spoken=str(payload.get("spoken") or payload.get("summary") or "").strip(),
        currency=currency,
        document=document,
    )


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


class GeminiVisionProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyze(
        self,
        image: bytes,
        mode: ReadMode,
        verbosity: Verbosity,
        question: str | None = None,
    ) -> AnalysisResult:
        import base64

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": analysis_prompt(mode, verbosity, question)},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64.b64encode(image).decode("ascii"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        try:
            response = httpx.post(
                url,
                params={"key": self.api_key},
                json=body,
                timeout=45.0,
            )
            response.raise_for_status()
            data = response.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if not text:
                raise UserFacingError(UNCLEAR_IMAGE, status_code=422)
            return result_from_payload(parse_json_object(text))
        except UserFacingError:
            raise
        except httpx.HTTPError as exc:
            logger.exception("Gemini vision request failed")
            raise UserFacingError(NETWORK_FAILURE, status_code=503) from exc
        except (ValueError, KeyError, IndexError) as exc:
            logger.exception("Gemini vision parse failed")
            raise UserFacingError(UNCLEAR_IMAGE, status_code=422) from exc


class OpenAIVisionProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyze(
        self,
        image: bytes,
        mode: ReadMode,
        verbosity: Verbosity,
        question: str | None = None,
    ) -> AnalysisResult:
        import base64

        data_url = "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii")
        body = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt(mode, verbosity, question)},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
                timeout=45.0,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            return result_from_payload(parse_json_object(text))
        except UserFacingError:
            raise
        except httpx.HTTPError as exc:
            logger.exception("OpenAI vision request failed")
            raise UserFacingError(NETWORK_FAILURE, status_code=503) from exc
        except (ValueError, KeyError, IndexError) as exc:
            logger.exception("OpenAI vision parse failed")
            raise UserFacingError(UNCLEAR_IMAGE, status_code=422) from exc


class NullVisionProvider:
    """Used in tests and when no AI key is configured."""

    name = "none"

    def analyze(
        self,
        image: bytes,
        mode: ReadMode,
        verbosity: Verbosity,
        question: str | None = None,
    ) -> AnalysisResult:
        raise UserFacingError(
            "Visual analysis isn't configured yet. Add an AI_API_KEY to enable reading.",
            status_code=503,
        )


def build_vision_provider(provider: str, api_key: str, model: str):
    if not api_key or provider == "none":
        return NullVisionProvider()
    if provider == "openai":
        return OpenAIVisionProvider(api_key=api_key, model=model)
    return GeminiVisionProvider(api_key=api_key, model=model)

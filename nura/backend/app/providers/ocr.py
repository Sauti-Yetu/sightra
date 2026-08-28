"""OCR providers. Vision models are the default; local engines can be swapped in."""

from __future__ import annotations

from app.providers.vision import GeminiVisionProvider, OpenAIVisionProvider
from app.schemas.common import AnalysisResult, ReadMode, Verbosity


class VisionOCRProvider:
    """OCR via the configured multimodal vision model."""

    name = "vision-ocr"

    def __init__(self, vision) -> None:
        self._vision = vision

    def extract_text(self, image: bytes) -> dict:
        if isinstance(self._vision, (GeminiVisionProvider, OpenAIVisionProvider)):
            result: AnalysisResult = self._vision.analyze(image, "read", "standard")
            return {
                "text": result.text,
                "paragraphs": [block for block in result.text.split("\n\n") if block.strip()],
                "confidence": result.confidence,
                "engine": self._vision.name,
            }
        return {"text": "", "paragraphs": [], "confidence": 0.0, "engine": "none"}


class StaticOCRProvider:
    """Deterministic provider for unit tests."""

    name = "static"

    def __init__(self, text: str = "", confidence: float = 0.9) -> None:
        self._text = text
        self._confidence = confidence

    def extract_text(self, image: bytes) -> dict:
        paragraphs = [block for block in self._text.split("\n\n") if block.strip()]
        return {
            "text": self._text,
            "paragraphs": paragraphs,
            "confidence": self._confidence,
            "engine": self.name,
        }

"""Provider protocols. Swap implementations without changing the API surface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.common import AnalysisResult, ReadMode, Verbosity


@runtime_checkable
class OCRProvider(Protocol):
    name: str

    def extract_text(self, image: bytes) -> dict:
        """Return text blocks while preserving reading order where possible."""


@runtime_checkable
class VisionProvider(Protocol):
    name: str

    def analyze(
        self,
        image: bytes,
        mode: ReadMode,
        verbosity: Verbosity,
        question: str | None = None,
    ) -> AnalysisResult:
        """Multimodal visual understanding of an image."""


@runtime_checkable
class CurrencyProvider(Protocol):
    name: str

    def identify(self, image: bytes, ocr_text: str, verbosity: Verbosity) -> dict:
        """Identify currency, targeting Kenyan Shilling notes in the MVP."""


@runtime_checkable
class ContextProvider(Protocol):
    def get(self, session_id: str) -> dict | None: ...

    def save_scan(self, session_id: str, result: AnalysisResult) -> None: ...

    def add_turn(self, session_id: str, role: str, content: str) -> None: ...

    def clear(self, session_id: str) -> None: ...


@runtime_checkable
class SpeechProvider(Protocol):
    name: str

    def synthesize(self, text: str, speed: float = 1.0) -> bytes: ...

    def transcribe(self, audio: bytes, mime_type: str = "audio/webm") -> str: ...

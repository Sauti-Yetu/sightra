"""Shared response envelopes."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ReadMode = Literal["read", "currency", "sign", "document", "ask"]
Verbosity = Literal["concise", "standard", "detailed"]
ContentType = Literal[
    "text",
    "document",
    "sign",
    "currency",
    "chart",
    "table",
    "screen",
    "label",
    "other",
]


class AudioPayload(BaseModel):
    url: str | None = None
    mime_type: str = "audio/mpeg"
    base64: str | None = None


class CurrencyResult(BaseModel):
    currency: str = "KES"
    denomination: int | None = None
    confidence: float = 0.0
    spoken: str = ""


class DocumentFields(BaseModel):
    document_type: str | None = None
    audience: str | None = None
    dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    action_required: str | None = None
    sections: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    type: ContentType = "text"
    confidence: float = 0.0
    text: str = ""
    title: str | None = None
    important_information: list[str] = Field(default_factory=list)
    summary: str = ""
    spoken: str = ""
    currency: CurrencyResult | None = None
    document: DocumentFields | None = None


class ApiResponse(BaseModel):
    success: bool
    type: str | None = None
    result: dict[str, Any] | None = None
    audio: AudioPayload | None = None
    confidence: float | None = None
    spoken: str | None = None
    session_id: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str

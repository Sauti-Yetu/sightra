"""Spoken wording helpers when the model omits a spoken field."""

from __future__ import annotations

from app.providers.currency import spoken_for_kes
from app.schemas.common import AnalysisResult, Verbosity


def ensure_spoken(result: AnalysisResult, verbosity: Verbosity) -> AnalysisResult:
    if result.spoken.strip():
        return result
    if result.currency and result.currency.denomination:
        result.spoken = spoken_for_kes(
            result.currency.denomination,
            verbosity,
            result.confidence >= 0.7,
        )
        return result
    if result.type == "sign" and result.text:
        title = result.title or result.text.split("\n")[0]
        if verbosity == "concise":
            result.spoken = title
        else:
            result.spoken = f"The sign reads {title}."
        return result
    if result.summary:
        result.spoken = result.summary
        return result
    if result.text:
        snippet = result.text.strip()
        if verbosity == "concise":
            result.spoken = snippet[:280]
        else:
            result.spoken = snippet[:800]
        return result
    result.spoken = "I couldn't find readable text in this image."
    return result

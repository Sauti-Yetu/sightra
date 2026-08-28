"""Kenyan Shilling recognition helpers. Additional currencies can be added later."""

from __future__ import annotations

import re

from app.schemas.common import Verbosity

KES_DENOMINATIONS = (50, 100, 200, 500, 1000)

_WORD = {
    50: "fifty",
    100: "one hundred",
    200: "two hundred",
    500: "five hundred",
    1000: "one thousand",
}


def spoken_for_kes(denomination: int, verbosity: Verbosity, confident: bool) -> str:
    words = _WORD.get(denomination, str(denomination))
    if not confident:
        if verbosity == "concise":
            return f"I believe this is {words} Kenyan shillings, but I'm not completely certain."
        return (
            f"I believe this is a {_note_phrase(denomination)} Kenyan shilling note, "
            "but I'm not completely certain."
        )
    if verbosity == "concise":
        return f"{words.capitalize()} Kenyan shillings."
    if verbosity == "detailed":
        return f"This appears to be a Kenyan {words} shilling banknote."
    return f"This is a {_note_phrase(denomination)} Kenyan shilling note."


def _note_phrase(denomination: int) -> str:
    return _WORD.get(denomination, str(denomination))


def denomination_from_text(text: str) -> int | None:
    compact = re.sub(r"[\s,]", "", text.upper())
    for value in sorted(KES_DENOMINATIONS, reverse=True):
        if re.search(rf"(?:KES|KSH|SHILLING)?{value}\b", compact) or str(value) in compact:
            if f"KES{value}" in compact or f"KSH{value}" in compact:
                return value
    for value in sorted(KES_DENOMINATIONS, reverse=True):
        pattern = rf"\b(?:KES|KSH|SHILLINGS?|SHILLING)?\s*{value}\b"
        if re.search(pattern, text, re.IGNORECASE):
            return value
    numbers = [int(match) for match in re.findall(r"\b(50|100|200|500|1000)\b", text)]
    if numbers:
        return numbers[0]
    return None


class CurrencyService:
    name = "kes-currency"

    def identify_from_analysis(
        self,
        denomination: int | None,
        confidence: float,
        verbosity: Verbosity,
        ocr_text: str = "",
    ) -> dict:
        value = denomination if denomination in KES_DENOMINATIONS else denomination_from_text(ocr_text)
        if value is None:
            return {
                "currency": "KES",
                "denomination": None,
                "confidence": min(confidence, 0.3),
                "spoken": "I couldn't confidently identify the denomination.",
            }
        confident = confidence >= 0.7
        return {
            "currency": "KES",
            "denomination": value,
            "confidence": confidence if value == denomination else min(confidence, 0.6),
            "spoken": spoken_for_kes(value, verbosity, confident),
        }

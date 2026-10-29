"""Lookout-style reading: send the image to Gemini and return spoken + transcript text."""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
logger = logging.getLogger(__name__)

MODES = ("live", "document", "currency", "signage", "upload")

LANGUAGE_NAMES = {
    "en": "English",
    "sw": "Swahili",
    "fr": "French",
    "ar": "Arabic",
    "so": "Somali",
    "ki": "Kikuyu",
}

MODE_INSTRUCTIONS = {
    "live": (
        "Read all visible text in natural reading order. "
        "If there is no text, briefly say what is in front of the camera."
    ),
    "document": (
        "This is a document, letter, or printed page. Transcribe it fully in reading order. "
        "Keep headings. Do not summarise unless the page is unreadable."
    ),
    "currency": (
        "Identify banknotes or coins. State currency, denomination, and country if visible. "
        "If none, say no currency was found."
    ),
    "signage": (
        "Read signs, labels, posters, menus, and wayfinding. Mention position only if it helps "
        "(left, right, above). Ignore decorative textures."
    ),
    "upload": (
        "Extract all useful text and describe important visuals for a blind user. "
        "Prefer a faithful transcript over a summary."
    ),
}


def _decode_image(frame_data: str) -> Image.Image | None:
    raw = frame_data or ""
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        blob = base64.b64decode(raw)
        img = Image.open(io.BytesIO(blob))
        img.load()
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        return img
    except Exception:
        logger.exception("Could not decode reader image")
        return None


def _parse_model_text(text: str) -> dict:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            spoken = str(data.get("spoken") or data.get("summary") or "").strip()
            body = str(data.get("text") or data.get("transcript") or "").strip()
            if spoken or body:
                return {"spoken": spoken or body, "text": body or spoken}
    except json.JSONDecodeError:
        pass
    parts = re.split(r"\n\s*\n", cleaned, maxsplit=1)
    spoken = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else spoken
    return {"spoken": spoken, "text": body}


def analyze_reader_image(
    frame_data: str,
    *,
    mode: str = "live",
    language: str = "en",
) -> dict:
    mode = mode if mode in MODES else "live"
    language = language if language in LANGUAGE_NAMES else "en"
    img = _decode_image(frame_data)
    if img is None:
        return {
            "success": False,
            "error": "Could not read the image.",
            "spoken": "I could not read that image.",
            "text": "",
            "mode": mode,
            "language": language,
        }

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        lang_name = LANGUAGE_NAMES[language]
        prompt = (
            "You are Sightra Reader, assisting a blind or low-vision user, similar to Google Lookout. "
            f"Task: {MODE_INSTRUCTIONS[mode]}\n"
            f"Write the spoken summary and the on-screen transcript in {lang_name}.\n"
            "Return JSON only with keys spoken and text. "
            "spoken: one or two short sentences for text-to-speech. "
            "text: the full transcript the user can review on screen. "
            "Do not invent text that is not visible. If unsure, say so."
        )
        response = model.generate_content([prompt, img])
        parsed = _parse_model_text(getattr(response, "text", "") or "")
        return {
            "success": True,
            "spoken": parsed["spoken"],
            "text": parsed["text"],
            "mode": mode,
            "language": language,
        }
    except Exception:
        logger.exception("Reader Gemini analysis failed")
        return {
            "success": False,
            "error": "Reading failed. Try again.",
            "spoken": "Reading failed. Try again.",
            "text": "",
            "mode": mode,
            "language": language,
        }

import base64
import io
import logging

from apps.vision.priorities import build_hazard_alert
from apps.vision.tasks import process_frame_vision_pipeline

from .services import GeminiAnalyzer, _brief_from_objects

logger = logging.getLogger(__name__)

analyzer = GeminiAnalyzer()


def _merge_audio_message(hazard_alert: str | None, analysis_text: str) -> str:
    """Ensure urgent cues are spoken even when Gemini returns a soft description."""
    if not hazard_alert:
        return analysis_text
    if not analysis_text:
        return hazard_alert
    first = analysis_text.split(".")[0].lower()
    if any(k in first for k in ("urgent", "caution", "stop", "vehicle", "wait")):
        return analysis_text
    return f"{hazard_alert} {analysis_text}"


def _decode_pil(frame_data):
    try:
        from PIL import Image

        raw = frame_data or ""
        if "," in raw and raw.strip().startswith("data:"):
            raw = raw.split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(raw)))
        img.load()
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((384, 384))
        return img
    except Exception:
        logger.exception("Could not decode vision frame for Gemini")
        return None


def analyze_frame_context(
    frame_data,
    text_prompt=None,
    run_vision_first=True,
    frame_id=1,
    narration_mode="auto",
    force_refresh=False,
):
    vision_metadata = {}

    if run_vision_first:
        vision_metadata = process_frame_vision_pipeline(frame_data, frame_id)

    hazard_alert = vision_metadata.get("hazard_alert") or build_hazard_alert(
        vision_metadata.get("objects") or []
    )
    objects = vision_metadata.get("objects") or []
    user_asked = bool((text_prompt or "").strip())

    use_fast = narration_mode == "fast" and not user_asked
    if use_fast:
        analysis_text = hazard_alert or _brief_from_objects(objects)
        return {
            "analysis_text": analysis_text,
            "vision_metadata": vision_metadata,
            "warnings": vision_metadata.get("warnings") or [],
            "hazard_alert": hazard_alert,
            "narration_mode": "fast",
        }

    should_force = force_refresh or bool(hazard_alert) or user_asked or not objects
    image = _decode_pil(frame_data)
    analysis_text = analyzer.analyze_scene(
        vision_metadata,
        text_prompt or "Describe obstacles and the path ahead for a blind user.",
        force_refresh=should_force,
        image=image,
    )
    analysis_text = _merge_audio_message(hazard_alert, analysis_text)

    return {
        "analysis_text": analysis_text,
        "vision_metadata": vision_metadata,
        "warnings": vision_metadata.get("warnings") or [],
        "hazard_alert": hazard_alert,
        "narration_mode": "full",
    }

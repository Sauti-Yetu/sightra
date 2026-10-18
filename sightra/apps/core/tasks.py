from apps.vision.priorities import build_hazard_alert
from apps.vision.tasks import process_frame_vision_pipeline

from .services import GeminiAnalyzer

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


def _brief_detection_summary(objects: list) -> str:
    if not objects:
        return ""
    parts = []
    for obj in objects[:3]:
        label = (obj.get("label") or "object").replace("_", " ")
        pos = obj.get("position") or "ahead"
        dist = obj.get("distance_band") or "near"
        parts.append(f"{label} {dist} {pos}")
    return ". ".join(parts) + "."


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
        if hazard_alert:
            analysis_text = hazard_alert
        else:
            analysis_text = _brief_detection_summary(objects)
        return {
            "analysis_text": analysis_text,
            "vision_metadata": vision_metadata,
            "warnings": vision_metadata.get("warnings") or [],
            "hazard_alert": hazard_alert,
            "narration_mode": "fast",
        }

    should_force = force_refresh or bool(hazard_alert) or user_asked

    analysis_text = analyzer.analyze_scene(
        vision_metadata,
        text_prompt,
        force_refresh=should_force,
    )
    analysis_text = _merge_audio_message(hazard_alert, analysis_text)

    return {
        "analysis_text": analysis_text,
        "vision_metadata": vision_metadata,
        "warnings": vision_metadata.get("warnings") or [],
        "hazard_alert": hazard_alert,
        "narration_mode": "full",
    }

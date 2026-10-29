import json
import logging
import time

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.tasks import analyze_frame_context
from apps.privacy.services.consent_service import has_camera_consent, has_privacy_notice_ack

logger = logging.getLogger(__name__)


def live_map(request):
    return render(request, "live-map.html")


def _json_body(request) -> dict:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


@method_decorator(csrf_exempt, name="dispatch")
class NavigationStreamView(View):
    """Receive a camera frame and return object detections plus spoken guidance."""

    def post(self, request, *args, **kwargs):
        payload = _json_body(request)
        frame_data = payload.get("frame_data")
        text_prompt = payload.get("text_prompt") or payload.get("user_prompt")
        frame_id = payload.get("frame_id", int(time.time()))
        narration_mode = (payload.get("narration_mode") or "auto").lower()
        if narration_mode not in ("auto", "fast", "full"):
            narration_mode = "auto"
        if narration_mode == "auto":
            narration_mode = "full" if text_prompt else "fast"
        force_refresh = bool(payload.get("force_refresh")) or bool(text_prompt)

        if not frame_data:
            return JsonResponse({"error": "frame_data is required"}, status=400)

        if not has_privacy_notice_ack(request) or not has_camera_consent(request):
            return JsonResponse(
                {
                    "error": "consent_required",
                    "message": "Privacy acknowledgement and camera analysis consent are required before processing.",
                    "code": "consent_required",
                },
                status=403,
            )

        try:
            analysis_result = analyze_frame_context(
                frame_data=frame_data,
                text_prompt=text_prompt,
                run_vision_first=True,
                frame_id=frame_id,
                narration_mode=narration_mode,
                force_refresh=force_refresh,
            )
        except Exception:
            logger.exception("Vision stream analysis failed")
            return JsonResponse(
                {
                    "error": "analysis_failed",
                    "message": "Could not analyse the scene. Try scanning again.",
                    "analysis_text": "Could not analyse the scene. Try scanning again.",
                    "metadata": {"objects": []},
                    "warnings": [],
                    "hazard_alert": None,
                },
                status=500,
            )

        analysis_text = analysis_result.get("analysis_text") or ""
        metadata = analysis_result.get("vision_metadata") or {"objects": []}
        return JsonResponse(
            {
                "message": "Analysis completed successfully",
                "analysis_text": analysis_text,
                "audio_url": None,
                "metadata": metadata,
                "warnings": analysis_result.get("warnings") or [],
                "hazard_alert": analysis_result.get("hazard_alert"),
                "narration_mode": analysis_result.get("narration_mode", narration_mode),
                "detector_ready": bool(metadata.get("detector_ready")),
            },
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class RouteGuidanceView(View):
    def post(self, request):
        payload = _json_body(request)
        origin = payload.get("origin")
        destination = payload.get("destination")

        if not origin or not destination:
            return JsonResponse({"error": "Origin and destination are required"}, status=400)

        return JsonResponse(
            {
                "route_id": "route_12345",
                "instructions": [
                    "Head north on Main Street",
                    "Turn right onto 5th Avenue",
                    "Your destination is on the left",
                ],
                "distance": "1.2 km",
                "estimated_time": "15 mins walk",
            },
            status=200,
        )

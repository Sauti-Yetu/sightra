from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.tasks import analyze_frame_context
from apps.audio.tasks import generate_audio_feedback
from apps.privacy.services.consent_service import has_camera_consent, has_privacy_notice_ack
from django.shortcuts import render
import time

def live_map(request):
    return render(request, "live-map.html")

class NavigationStreamView(APIView):
    """
    Endpoint for receiving a video frame and returning AI audio guidance.
    """
    def post(self, request, *args, **kwargs):
        # 1. Parse Input
        frame_data = request.data.get("frame_data") # e.g. base64 image
        text_prompt = request.data.get("text_prompt") or request.data.get("user_prompt")
        frame_id = request.data.get("frame_id", int(time.time()))
        narration_mode = (request.data.get("narration_mode") or "auto").lower()
        if narration_mode not in ("auto", "fast", "full"):
            narration_mode = "auto"
        if narration_mode == "auto":
            narration_mode = "full" if text_prompt else "fast"
        force_refresh = bool(request.data.get("force_refresh")) or bool(text_prompt)

        if not frame_data:
            return Response({"error": "frame_data is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not has_privacy_notice_ack(request) or not has_camera_consent(request):
            return Response(
                {
                    "error": "consent_required",
                    "message": "Privacy acknowledgement and camera analysis consent are required before processing.",
                    "code": "consent_required",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2. Trigger asynchronous analysis pipeline (simulated sync wait for UI demonstration)
        # In a real deployed high-throughput system you could return a job_id 
        # and have the client connect via WebSocket or poll for result.
        # Here, we use .apply_async().get() or run it synchronously if we need 
        # immediate HTTP response for the blind user to not experience massive latency.
        
        # Analyze using Vision + Gemini
        analysis_result = analyze_frame_context(
            frame_data=frame_data,
            text_prompt=text_prompt,
            run_vision_first=True,
            frame_id=frame_id,
            narration_mode=narration_mode,
            force_refresh=force_refresh,
        )

        analysis_text = analysis_result.get("analysis_text") or ""

        audio_info = {"audio_url": None}
        if analysis_text and narration_mode == "full":
            audio_info = generate_audio_feedback(
                analysis_text, output_filename=f"response_{frame_id}.wav"
            )

        return Response(
            {
                "message": "Analysis completed successfully",
                "analysis_text": analysis_text,
                "audio_url": audio_info.get("audio_url"),
                "metadata": analysis_result.get("vision_metadata"),
                "warnings": analysis_result.get("warnings") or [],
                "hazard_alert": analysis_result.get("hazard_alert"),
                "narration_mode": analysis_result.get("narration_mode", narration_mode),
            },
            status=status.HTTP_200_OK,
        )

class RouteGuidanceView(APIView):
    """
    Endpoint for getting turn-by-turn navigation instructions.
    """
    def post(self, request):
        origin = request.data.get("origin")
        destination = request.data.get("destination")
        
        if not origin or not destination:
            return Response({"error": "Origin and destination are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mocking route guidance for now
        return Response({
            "route_id": "route_12345",
            "instructions": [
                "Head north on Main Street",
                "Turn right onto 5th Avenue",
                "Your destination is on the left"
            ],
            "distance": "1.2 km",
            "estimated_time": "15 mins walk"
        }, status=status.HTTP_200_OK)

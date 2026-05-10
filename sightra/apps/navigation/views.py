from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.tasks import analyze_frame_context
from apps.audio.tasks import generate_audio_feedback
import time

class NavigationStreamView(APIView):
    """
    Endpoint for receiving a video frame and returning AI audio guidance.
    """
    def post(self, request, *args, **kwargs):
        # 1. Parse Input
        frame_data = request.data.get("frame_data") # e.g. base64 image
        text_prompt = request.data.get("text_prompt") # e.g. "Is the path clear?"
        frame_id = request.data.get("frame_id", int(time.time()))

        if not frame_data:
            return Response({"error": "frame_data is required"}, status=status.HTTP_400_BAD_REQUEST)

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
            frame_id=frame_id
        )
        
        analysis_text = analysis_result.get("analysis_text", "Path clear. Proceed with caution.")
        
        # 3. Generate Audio Feedback
        # This can also be asynchronous, but we return the URL or text
        audio_info = generate_audio_feedback(analysis_text, output_filename=f"response_{frame_id}.wav")
        
        return Response({
            "message": "Analysis completed successfully",
            "analysis_text": analysis_text,
            "audio_url": audio_info.get("audio_url"),
            "metadata": analysis_result.get("vision_metadata")
        }, status=status.HTTP_200_OK)

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

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
        frame_data = request.data.get("frame_data")
        text_prompt = request.data.get("text_prompt")
        frame_id = request.data.get("frame_id", int(time.time()))

        if not frame_data:
            return Response({"error": "frame_data is required"}, status=status.HTTP_400_BAD_REQUEST)

        analysis_result = analyze_frame_context(
            frame_data=frame_data,
            text_prompt=text_prompt,
            run_vision_first=True,
            frame_id=frame_id,
        )

        analysis_text = analysis_result.get("analysis_text", "Path clear. Proceed with caution.")

        fid = str(frame_id).replace("/", "_").replace("\\", "_")[:120]
        safe_name = f"response_{fid}.wav"

        audio_info = generate_audio_feedback(analysis_text, output_filename=safe_name)

        return Response(
            {
                "message": "Analysis completed successfully",
                "analysis_text": analysis_text,
                "audio_url": audio_info.get("audio_url"),
                "metadata": analysis_result.get("vision_metadata"),
            },
            status=status.HTTP_200_OK,
        )

import base64
import uuid
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .services import analyze_scene

# Create your views here.
def vision(request):
    return render(request, "vision.html")

@method_decorator(csrf_exempt, name="dispatch")
class SceneAnalysisView(View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON body"
            }, status=400)

        frame_data = payload.get("frame_data")
        text_prompt = payload.get("text_prompt", "Describe the scene and navigation guidance.")
        device_id = payload.get("device_id")
        language = payload.get("language", "en")

        if not frame_data:
            return JsonResponse({
                "success": False,
                "error": "frame_data is required"
            }, status=400)

        try:
            result = analyze_scene(
                frame_data=frame_data,
                text_prompt=text_prompt,
                device_id=device_id,
                language=language
            )

            return JsonResponse({
                "success": True,
                "request_id": str(uuid.uuid4()),
                "device_id": device_id,
                "language": language,
                "analysis_text": result.get("analysis_text"),
                "navigation_hint": result.get("navigation_hint"),
                "objects": result.get("objects", []),
                "warnings": result.get("warnings", []),
                "metadata": result.get("metadata", {})
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)
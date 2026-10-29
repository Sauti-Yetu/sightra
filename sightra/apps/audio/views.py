import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .elevenlabs import synthesize


def voice_assistant(request):
    return render(request, "voice_assistant.html")


@csrf_exempt
@require_POST
def speak(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    text = (payload.get("text") or "").strip()
    gender = (payload.get("gender") or "female").lower()
    if gender not in ("male", "female"):
        gender = "female"
    if not text:
        return JsonResponse({"success": False, "error": "text is required"}, status=400)

    audio, content_type = synthesize(text, gender=gender)
    if not audio:
        return JsonResponse(
            {
                "success": False,
                "fallback": True,
                "error": "Cloud voice is unavailable. Using the device voice instead.",
            },
            status=503,
        )
    response = HttpResponse(audio, content_type=content_type)
    response["Cache-Control"] = "no-store"
    return response

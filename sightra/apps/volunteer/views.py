import os
from django.shortcuts import render
from django.http import JsonResponse
from livekit import api
from django.conf import settings

# Create your views here.
def sightra_connect(request):
    return render(request, "sightra-connect.html")


def live_call(request):
    # Pass LiveKit URL to template
    livekit_url = os.getenv("LIVEKIT_URL", "wss://sightra-demo.livekit.cloud")
    return render(request, "live-call.html", {"livekit_url": livekit_url})


def get_livekit_token(request):
    room_name = request.GET.get("room", "sightra-call")
    participant_name = request.GET.get("name", "User")
    
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        return JsonResponse({"error": "LiveKit credentials not configured"}, status=500)

    token = api.AccessToken(api_key, api_secret) \
        .with_identity(participant_name) \
        .with_name(participant_name) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
    
    return JsonResponse({"token": token.to_jwt()})



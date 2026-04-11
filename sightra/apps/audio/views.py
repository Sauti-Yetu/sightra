from django.shortcuts import render

# Create your views here.
def voice_assistant(request):
    return render(request, "voice_assistant.html")
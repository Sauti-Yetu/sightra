from django.shortcuts import render

def index(request):
    return render(request, "index.html")

def vision(request):
    return render(request, "vision.html")

def settings_view(request):
    return render(request, "settings.html")

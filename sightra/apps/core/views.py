from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from django.conf import settings
import os


def dashboard(request):
    return render(request, "dashboard.html")


def landing_page(request):
    return render(request, "landing-page.html")


def offline_page(request):
    return render(request, "offline.html")


def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, "static", "js", "sw.js")
    with open(sw_path, "rb") as sw_file:
        content = sw_file.read()
    response = HttpResponse(content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def web_manifest(request):
    manifest_path = os.path.join(settings.BASE_DIR, "static", "manifest.webmanifest")
    with open(manifest_path, "rb") as manifest_file:
        content = manifest_file.read()
    return HttpResponse(content, content_type="application/manifest+json")


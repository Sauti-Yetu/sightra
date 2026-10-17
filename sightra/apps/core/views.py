from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render


def dashboard(request):
    return render(request, "dashboard.html")


def landing_page(request):
    if getattr(request, "sightra_user", None):
        from django.shortcuts import redirect

        return redirect("/dashboard")
    return render(request, "landing-page.html")


def offline_page(request):
    return render(request, "offline.html")


def _static_file(name: str, content_type: str):
    path = Path(settings.BASE_DIR) / "static" / name
    if not path.is_file():
        raise Http404
    return FileResponse(path.open("rb"), content_type=content_type)


def service_worker(request):
    response = _static_file("js/sw.js", "application/javascript; charset=utf-8")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def web_manifest(request):
    response = _static_file("manifest.webmanifest", "application/manifest+json")
    response["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    return response


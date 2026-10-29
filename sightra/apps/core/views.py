from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


def _display_name_for(user):
    """First-name label from the signed-in account. Never returns a full email.

    Kept in this module so /dashboard does not depend on a Passenger-cached
    session_service.py from a previous deploy.
    """
    if not isinstance(user, dict) or not user:
        return ""
    cached = str(user.get("display_name") or "").strip()
    if cached and "@" not in cached:
        return cached.split()[0]
    meta = user.get("user_metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    for key in ("given_name", "full_name", "name", "preferred_username"):
        raw = str(meta.get(key) or "").strip()
        if raw:
            return raw.split()[0]
    email = str(user.get("email") or "").strip()
    local = email.split("@")[0].strip() if email else ""
    if not local:
        return ""
    pretty = local.replace(".", " ").replace("_", " ").replace("-", " ").strip()
    first = pretty.split()[0] if pretty else ""
    return first[:1].upper() + first[1:] if first else ""


def dashboard(request):
    user = getattr(request, "sightra_user", None)
    return render(
        request,
        "dashboard.html",
        {
            "display_name": _display_name_for(user),
            "signed_in": bool(user),
        },
    )


@ensure_csrf_cookie
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


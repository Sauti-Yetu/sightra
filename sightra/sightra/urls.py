"""
URL configuration for sightra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from apps.core.views import *
from apps.audio.views import *
from apps.vision.views import *
from apps.settings.views import *
from apps.accounts.views import *
from apps.volunteer.views import *
from apps.navigation.views import *
from apps.privacy import views as privacy_views


urlpatterns = [
    path("admin/", admin.site.urls),
    # Authentication 
    path("signin/", signin, name="signin"),
    path("signup/", signup, name="signup"),
    path("signout/", signout, name="signout"),
    path("auth/google/", auth_google, name="auth-google"),
    path("auth/callback/", auth_callback, name="auth-callback"),
    path("offline/", offline_page, name="offline"),
    path("sw.js", service_worker, name="service-worker"),
    path("manifest.webmanifest", web_manifest, name="web-manifest"),
    # Homepage
    path("dashboard", dashboard, name="dashboard"),
    path("", landing_page, name="landing_page"),
    # Vision 
    path("vision/", vision, name="vision"),
    # Voice assistant
    path("voice_assistant/", voice_assistant, name="voice_assistant"),
    # Navigation
    path('live-map/', live_map, name="live-map"),
    # Volunteer
    path("sightra-connect/", sightra_connect, name="sightra-connect"),
    path("live-call/", live_call, name="live-call"),
    path("api/volunteer/token/", get_livekit_token, name="get-livekit-token"),
    # User settings
    path("settings/", settings_view, name="settings"),
    path("settings/privacy/", privacy_views.privacy_settings, name="privacy-settings"),
    path("legal/", privacy_views.legal_index, name="legal-index"),
    path("legal/rights/", privacy_views.privacy_rights, name="privacy-rights"),
    path("legal/business/", privacy_views.business_details, name="legal-business"),
    path("legal/unsubscribe/", privacy_views.unsubscribe, name="legal-unsubscribe"),
    path("unsubscribe/", privacy_views.unsubscribe, name="unsubscribe"),
    path("legal/parental-consent/", privacy_views.parental_consent, name="legal-parental"),
    path("legal/<slug:slug>/", privacy_views.legal_document, name="legal-document"),
    # APIs
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/audio/", include("apps.audio.urls")),
    path("api/vision/", include("apps.vision.urls")),
    path("api/navigation/", include("apps.navigation.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/settings/", include("apps.settings.urls")),
    path("api/privacy/", include("apps.privacy.urls")),
]

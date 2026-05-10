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


urlpatterns = [
    path("admin/", admin.site.urls),
    # Authentication 
    path("signin/", signin, name="signin"),
    path("signup/", signup, name="signup"),
    # Homepage
    path("", index, name="index"),
    path("landing-page/", landing_page, name="landing_page"),
    # Vision 
    path("vision/", vision, name="vision"),
    # Voice assistant
    path("voice_assistant/", voice_assistant, name="voice_assistant"),
    # Volunteer
    path("sightra-connect/", sightra_connect, name="sightra-connect"),
    path("live-call/", live_call, name="live-call"),
    # User settings
    path("settings/", settings_view, name="settings"),
    # APIs
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/audio/", include("apps.audio.urls")),
    path("api/vision/", include("apps.vision.urls")),
    path("api/navigation/", include("apps.navigation.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/settings/", include("apps.settings.urls")),
]

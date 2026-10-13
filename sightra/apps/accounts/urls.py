from django.urls import path

from .views import signout, update_theme_preference

urlpatterns = [
    path("signout/", signout, name="signout"),
    path("theme/", update_theme_preference, name="update_theme"),
]

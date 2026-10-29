from django.urls import path

from .views import speak

urlpatterns = [
    path("speak/", speak, name="audio-speak"),
]

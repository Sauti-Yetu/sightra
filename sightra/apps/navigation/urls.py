from django.urls import path
from .views import NavigationStreamView

urlpatterns = [
    path("stream/", NavigationStreamView.as_view(), name="navigation_stream"),
]

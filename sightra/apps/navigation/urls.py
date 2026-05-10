from .views import NavigationStreamView, RouteGuidanceView
from django.urls import path

urlpatterns = [
    path("stream/", NavigationStreamView.as_view(), name="navigation_stream"),
    path("route/", RouteGuidanceView.as_view(), name="navigation_route"),
]

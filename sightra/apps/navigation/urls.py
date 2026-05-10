from .views import NavigationStreamView, RouteGuidanceView

urlpatterns = [
    path("stream/", NavigationStreamView.as_view(), name="navigation_stream"),
    path("route/", RouteGuidanceView.as_view(), name="navigation_route"),
]

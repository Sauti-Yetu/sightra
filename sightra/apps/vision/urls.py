from django.urls import path

from .views import ObjectDetectionView, SceneAnalysisView

urlpatterns = [
    path("detect/", ObjectDetectionView.as_view(), name="vision_detect"),
    path("analyze/", SceneAnalysisView.as_view(), name="vision_analyze"),
]

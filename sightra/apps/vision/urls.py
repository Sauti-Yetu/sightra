from django.urls import path

from .views import *

urlpatterns = [
    path("api/vision/analyze/", SceneAnalysisView.as_view(), name="scene_analysis_api"),
]

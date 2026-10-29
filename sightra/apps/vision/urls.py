from django.urls import path

from .views import ReaderAnalyzeView, SceneAnalysisView

urlpatterns = [
    path("analyze/", SceneAnalysisView.as_view(), name="scene_analysis_api"),
    path("reader/analyze/", ReaderAnalyzeView.as_view(), name="reader_analyze_api"),
]

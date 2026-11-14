"""Analysis URL patterns."""

from django.urls import path

from .views import AnalysisJobDetailView, AnalysisJobListView, PlaygroundView, SubmitAnalysisView

urlpatterns = [
    path("analysis/", SubmitAnalysisView.as_view(), name="analysis-submit"),
    path("analysis/list/", AnalysisJobListView.as_view(), name="analysis-list"),
    path("analysis/<uuid:pk>/", AnalysisJobDetailView.as_view(), name="analysis-detail"),
    path("playground/", PlaygroundView.as_view(), name="playground"),
]

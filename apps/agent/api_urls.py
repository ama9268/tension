from django.urls import path

from .views import AnalysisListView, AnalysisRequestView

urlpatterns = [
    path("analyze/", AnalysisRequestView.as_view(), name="agent-analyze"),
    path("analyses/", AnalysisListView.as_view(), name="agent-analyses"),
]

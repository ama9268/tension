from django.urls import path

from .views import ChartsView

urlpatterns = [
    path("", ChartsView.as_view(), name="charts"),
]

from django.urls import path

from .views import chart_data_api

urlpatterns = [
    path("analytics/chart/", chart_data_api, name="analytics-chart-api"),
]

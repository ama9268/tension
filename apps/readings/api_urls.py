from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BloodPressureReadingViewSet

router = DefaultRouter()
router.register(r"readings", BloodPressureReadingViewSet, basename="reading-api")

urlpatterns = [
    path("", include(router.urls)),
]

from django.urls import path

from .views import ApiKeyCreateView, ApiKeyRevokeView, ProfileView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("api-keys/nueva/", ApiKeyCreateView.as_view(), name="apikey-create"),
    path("api-keys/<int:pk>/revocar/", ApiKeyRevokeView.as_view(), name="apikey-revoke"),
]

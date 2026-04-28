from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth Web
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/", include("apps.accounts.urls")),

    # Auth API
    path("api/v1/token/", obtain_auth_token, name="api-token"),
    path("api/v1/jwt/", TokenObtainPairView.as_view(), name="jwt-obtain"),
    path("api/v1/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),

    # Apps web
    path("", include("apps.dashboard.urls")),
    path("lecturas/", include("apps.readings.urls")),
    path("graficas/", include("apps.analytics.urls")),
    path("agente/", include("apps.agent.urls")),

    # API REST
    path("api/v1/", include("apps.readings.api_urls")),
    path("api/v1/", include("apps.analytics.api_urls")),
    path("api/v1/agent/", include("apps.agent.api_urls")),
    path("", include("apps.readings.health_urls")),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

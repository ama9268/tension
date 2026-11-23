from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import ApiKey


class ReadOnlyIfApiKey(BasePermission):
    """Las API keys solo pueden usar métodos seguros (GET/HEAD/OPTIONS)."""

    message = "Las API keys son de solo lectura."

    def has_permission(self, request, view) -> bool:
        if isinstance(request.auth, ApiKey):
            return request.method in SAFE_METHODS
        return True

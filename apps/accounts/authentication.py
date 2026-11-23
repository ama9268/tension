from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import ApiKey

logger = logging.getLogger(__name__)

KEYWORD = "ApiKey"
TOUCH_INTERVAL = timedelta(minutes=5)


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """Cabecera `Authorization: ApiKey <clave>`."""

    def authenticate_header(self, request) -> str:
        return KEYWORD

    def authenticate(self, request):
        parts = authentication.get_authorization_header(request).split()
        if not parts or parts[0].decode(errors="ignore") != KEYWORD:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Cabecera ApiKey inválida.")
        raw = parts[1].decode(errors="ignore")
        key = (
            ApiKey.objects.select_related("user")
            .filter(key_hash=ApiKey.hash_key(raw), revoked=False, user__is_active=True)
            .first()
        )
        if key is None:
            logger.warning("ApiKey rechazada")
            raise exceptions.AuthenticationFailed("API key inválida o revocada.")
        now = timezone.now()
        if key.last_used_at is None or now - key.last_used_at > TOUCH_INTERVAL:
            ApiKey.objects.filter(pk=key.pk).update(last_used_at=now)
        return key.user, key

from __future__ import annotations

import hashlib
import secrets

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    notes = models.TextField(blank=True)
    medical_context = models.TextField(
        blank=True,
        verbose_name="Contexto médico personal",
        help_text="Edad, peso, actividad física, tipo de trabajo, medicación habitual, etc.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self) -> str:
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class ApiKey(models.Model):
    """Credencial de solo lectura para apps externas. Solo se guarda el hash."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys", db_index=True)
    name = models.CharField(max_length=80)
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    prefix = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "API key"
        verbose_name_plural = "API keys"

    def __str__(self) -> str:
        return f"{self.name} ({self.prefix}…) — {self.user.username}"

    @staticmethod
    def hash_key(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def create_for(cls, user: User, name: str) -> tuple["ApiKey", str]:
        raw = "tk_" + secrets.token_urlsafe(32)
        obj = cls.objects.create(
            user=user, name=name, key_hash=cls.hash_key(raw), prefix=raw[:8]
        )
        return obj, raw

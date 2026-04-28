from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class AgentAnalysis(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="analyses"
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    date_from = models.DateField()
    date_to = models.DateField()
    reading_count = models.IntegerField()
    analysis_text = models.TextField()
    model_used = models.CharField(max_length=50, default="claude-sonnet-4-6")

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "Análisis del agente"
        verbose_name_plural = "Análisis del agente"

    def __str__(self) -> str:
        return (
            f"{self.user.username} — análisis {self.date_from} a {self.date_to} "
            f"({self.reading_count} lecturas)"
        )

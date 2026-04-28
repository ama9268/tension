from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class BloodPressureReading(models.Model):
    TIME_OF_DAY = [
        ("morning", "Mañana"),
        ("afternoon", "Tarde"),
        ("evening", "Noche"),
        ("night", "Madrugada"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="readings", db_index=True
    )
    systolic = models.PositiveSmallIntegerField(help_text="mmHg")
    diastolic = models.PositiveSmallIntegerField(help_text="mmHg")
    pulse = models.PositiveSmallIntegerField(null=True, blank=True, help_text="ppm")
    measured_at = models.DateTimeField(db_index=True)
    time_of_day = models.CharField(max_length=10, choices=TIME_OF_DAY, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-measured_at"]
        verbose_name = "Lectura de presión arterial"
        verbose_name_plural = "Lecturas de presión arterial"
        indexes = [
            models.Index(fields=["user", "measured_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.user.username} — {self.systolic}/{self.diastolic} "
            f"@ {self.measured_at:%Y-%m-%d %H:%M}"
        )

    def classification(self) -> str:
        """Clasificación según guías AHA/ACC 2017."""
        if self.systolic > 180 or self.diastolic > 120:
            return "crisis"
        if self.systolic >= 140 or self.diastolic >= 90:
            return "hypertension_2"
        if self.systolic >= 130 or self.diastolic >= 80:
            return "hypertension_1"
        if self.systolic >= 120 and self.diastolic < 80:
            return "elevated"
        return "normal"

    @property
    def classification_label(self) -> str:
        labels = {
            "normal": "Normal",
            "elevated": "Elevada",
            "hypertension_1": "HTA Estadio 1",
            "hypertension_2": "HTA Estadio 2",
            "crisis": "Crisis hipertensiva",
        }
        return labels.get(self.classification(), "—")

    @property
    def classification_color(self) -> str:
        """Clases Tailwind para la etiqueta de clasificación."""
        colors = {
            "normal": "bg-green-100 text-green-800",
            "elevated": "bg-yellow-100 text-yellow-800",
            "hypertension_1": "bg-orange-100 text-orange-800",
            "hypertension_2": "bg-red-100 text-red-800",
            "crisis": "bg-red-900 text-white",
        }
        return colors.get(self.classification(), "bg-gray-100 text-gray-800")

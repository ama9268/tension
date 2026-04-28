from __future__ import annotations

import csv
import io
from datetime import datetime, timezone as dt_timezone

from rest_framework import serializers

from .models import BloodPressureReading

# Límites médicos validados
_LIMITS: dict[str, tuple[int, int]] = {
    "systolic": (50, 300),
    "diastolic": (30, 200),
    "pulse": (30, 220),
}


class BloodPressureReadingSerializer(serializers.ModelSerializer):
    classification = serializers.SerializerMethodField()
    classification_label = serializers.SerializerMethodField()

    class Meta:
        model = BloodPressureReading
        fields = [
            "id",
            "systolic",
            "diastolic",
            "pulse",
            "measured_at",
            "time_of_day",
            "notes",
            "created_at",
            "classification",
            "classification_label",
        ]
        read_only_fields = ["id", "created_at", "classification", "classification_label"]

    def get_classification(self, obj: BloodPressureReading) -> str:
        return obj.classification()

    def get_classification_label(self, obj: BloodPressureReading) -> str:
        return obj.classification_label

    def validate_systolic(self, value: int) -> int:
        lo, hi = _LIMITS["systolic"]
        if not (lo <= value <= hi):
            raise serializers.ValidationError(
                f"Sistólica fuera del rango médico [{lo}, {hi}] mmHg"
            )
        return value

    def validate_diastolic(self, value: int) -> int:
        lo, hi = _LIMITS["diastolic"]
        if not (lo <= value <= hi):
            raise serializers.ValidationError(
                f"Diastólica fuera del rango médico [{lo}, {hi}] mmHg"
            )
        return value

    def validate_pulse(self, value: int | None) -> int | None:
        if value is None:
            return value
        lo, hi = _LIMITS["pulse"]
        if not (lo <= value <= hi):
            raise serializers.ValidationError(
                f"Pulso fuera del rango médico [{lo}, {hi}] ppm"
            )
        return value

    def validate(self, data: dict) -> dict:
        sys = data.get("systolic")
        dia = data.get("diastolic")
        if sys and dia and dia >= sys:
            raise serializers.ValidationError(
                "La diastólica no puede ser mayor o igual que la sistólica."
            )
        return data


def readings_to_csv(queryset) -> str:
    """Convierte un queryset de lecturas a CSV."""
    fields = [
        "id", "systolic", "diastolic", "pulse",
        "measured_at", "time_of_day", "notes", "created_at",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in queryset.values(*fields):
        for key in ("measured_at", "created_at"):
            val = row.get(key)
            if isinstance(val, datetime):
                row[key] = val.astimezone(dt_timezone.utc).isoformat()
        writer.writerow(row)
    return output.getvalue()

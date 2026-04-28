from __future__ import annotations

from django.db.models import Avg, Max, Min
from django.db.models.functions import TruncDate

from apps.readings.models import BloodPressureReading


def get_chart_data(user, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
    """Datos diarios agregados para Chart.js (promedio, máximo, mínimo por día)."""
    qs = BloodPressureReading.objects.filter(user=user)
    if date_from:
        qs = qs.filter(measured_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(measured_at__date__lte=date_to)

    daily = (
        qs.annotate(day=TruncDate("measured_at"))
        .values("day")
        .annotate(
            sys_avg=Avg("systolic"),
            sys_max=Max("systolic"),
            sys_min=Min("systolic"),
            dia_avg=Avg("diastolic"),
            dia_max=Max("diastolic"),
            dia_min=Min("diastolic"),
            pulse_avg=Avg("pulse"),
        )
        .order_by("day")
    )

    def _r(v: float | None, d: int = 1) -> float | None:
        return round(float(v), d) if v is not None else None

    return [
        {
            "date": row["day"].isoformat(),
            "sys_avg": _r(row["sys_avg"]),
            "sys_max": _r(row["sys_max"]),
            "sys_min": _r(row["sys_min"]),
            "dia_avg": _r(row["dia_avg"]),
            "dia_max": _r(row["dia_max"]),
            "dia_min": _r(row["dia_min"]),
            "pulse_avg": _r(row["pulse_avg"]),
        }
        for row in daily
    ]

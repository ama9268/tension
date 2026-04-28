from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone
from django.views.generic import TemplateView

from apps.readings.models import BloodPressureReading


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        ctx["latest_readings"] = BloodPressureReading.objects.filter(
            user=user
        ).order_by("-measured_at")[:10]

        ctx["latest"] = BloodPressureReading.objects.filter(
            user=user
        ).order_by("-measured_at").first()

        week_ago = timezone.now() - timedelta(days=7)
        week_qs = BloodPressureReading.objects.filter(user=user, measured_at__gte=week_ago)
        if week_qs.exists():
            ctx["week_stats"] = week_qs.aggregate(
                systolic_avg=Avg("systolic"),
                diastolic_avg=Avg("diastolic"),
                pulse_avg=Avg("pulse"),
                systolic_max=Max("systolic"),
                diastolic_max=Max("diastolic"),
                count=Count("id"),
            )
            for k, v in ctx["week_stats"].items():
                if isinstance(v, float):
                    ctx["week_stats"][k] = round(v, 1)
        else:
            ctx["week_stats"] = None

        ctx["total_readings"] = BloodPressureReading.objects.filter(user=user).count()

        return ctx

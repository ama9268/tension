from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_timezone

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .forms import BloodPressureReadingForm
from .models import BloodPressureReading
from .serializers import BloodPressureReadingSerializer, readings_to_csv

logger = logging.getLogger(__name__)


# ── Vistas Web ─────────────────────────────────────────────────────────────

class ReadingListView(LoginRequiredMixin, ListView):
    model = BloodPressureReading
    template_name = "readings/list.html"
    context_object_name = "readings"
    paginate_by = 20

    def get_queryset(self):
        qs = BloodPressureReading.objects.filter(user=self.request.user)
        date_from = self.request.GET.get("from")
        date_to = self.request.GET.get("to")
        if date_from:
            qs = qs.filter(measured_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(measured_at__date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["date_from"] = self.request.GET.get("from", "")
        ctx["date_to"] = self.request.GET.get("to", "")
        return ctx


class ReadingCreateView(LoginRequiredMixin, CreateView):
    model = BloodPressureReading
    form_class = BloodPressureReadingForm
    template_name = "readings/form.html"
    success_url = reverse_lazy("reading-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        logger.info("readings: nueva lectura para user=%s", self.request.user.username)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nueva lectura"
        ctx["btn_label"] = "Guardar lectura"
        return ctx


class ReadingUpdateView(LoginRequiredMixin, UpdateView):
    model = BloodPressureReading
    form_class = BloodPressureReadingForm
    template_name = "readings/form.html"
    success_url = reverse_lazy("reading-list")

    def get_queryset(self):
        # Seguridad: solo lecturas del usuario autenticado
        return BloodPressureReading.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Editar lectura"
        ctx["btn_label"] = "Actualizar lectura"
        return ctx


class ReadingDeleteView(LoginRequiredMixin, DeleteView):
    model = BloodPressureReading
    template_name = "readings/confirm_delete.html"
    success_url = reverse_lazy("reading-list")

    def get_queryset(self):
        return BloodPressureReading.objects.filter(user=self.request.user)


# ── API REST ────────────────────────────────────────────────────────────────

class BloodPressureReadingViewSet(viewsets.ModelViewSet):
    serializer_class = BloodPressureReadingSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["measured_at", "systolic", "diastolic"]
    ordering = ["-measured_at"]

    def get_queryset(self):
        # Seguridad: siempre filtrar por request.user
        qs = BloodPressureReading.objects.filter(user=self.request.user)
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        if date_from:
            qs = qs.filter(measured_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(measured_at__date__lte=date_to)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def export(self, request: Request) -> HttpResponse:
        qs = self.get_queryset()
        csv_data = readings_to_csv(qs)
        ts = datetime.now(dt_timezone.utc).strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(csv_data, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="tension_{ts}.csv"'
        return response

    @action(detail=False, methods=["get"])
    def stats(self, request: Request) -> Response:
        from django.db.models import Avg, Count, Max, Min

        qs = self.get_queryset()
        if not qs.exists():
            return Response(
                {"detail": "Sin datos en el período seleccionado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = qs.aggregate(
            systolic_avg=Avg("systolic"),
            systolic_max=Max("systolic"),
            systolic_min=Min("systolic"),
            diastolic_avg=Avg("diastolic"),
            diastolic_max=Max("diastolic"),
            diastolic_min=Min("diastolic"),
            pulse_avg=Avg("pulse"),
            count=Count("id"),
        )
        for k, v in data.items():
            if isinstance(v, float):
                data[k] = round(v, 1)
        return Response(data)

    @action(detail=False, methods=["get"])
    def chart(self, request: Request) -> Response:
        qs = self.get_queryset().order_by("measured_at")
        data = list(
            qs.values("measured_at", "systolic", "diastolic", "pulse", "time_of_day")
        )
        for row in data:
            if isinstance(row.get("measured_at"), datetime):
                row["measured_at"] = row["measured_at"].isoformat()
        return Response(data)

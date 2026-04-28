from __future__ import annotations

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AgentAnalysis
from .serializers import AgentAnalysisSerializer, AnalysisRequestSerializer
from .services import request_analysis

logger = logging.getLogger(__name__)


class AgentView(LoginRequiredMixin, TemplateView):
    template_name = "agent/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["analyses"] = AgentAnalysis.objects.filter(
            user=self.request.user
        ).order_by("-requested_at")[:10]
        return ctx


class AnalysisRequestView(APIView):
    def post(self, request):
        serializer = AnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = request_analysis(
                user=request.user,
                date_from=serializer.validated_data["date_from"],
                date_to=serializer.validated_data["date_to"],
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(
                "agent: error en análisis para user=%s: %s",
                request.user.username,
                exc,
                exc_info=True,
            )
            return Response(
                {"detail": "Error al conectar con el servicio de análisis. Inténtalo más tarde."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class AnalysisListView(generics.ListAPIView):
    serializer_class = AgentAnalysisSerializer

    def get_queryset(self):
        return AgentAnalysis.objects.filter(user=self.request.user)

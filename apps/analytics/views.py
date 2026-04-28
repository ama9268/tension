from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import get_chart_data


class ChartsView(LoginRequiredMixin, TemplateView):
    template_name = "analytics/charts.html"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chart_data_api(request):
    date_from = request.query_params.get("from")
    date_to = request.query_params.get("to")
    data = get_chart_data(request.user, date_from, date_to)
    return Response(data)

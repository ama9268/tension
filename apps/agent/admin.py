from django.contrib import admin

from .models import AgentAnalysis


@admin.register(AgentAnalysis)
class AgentAnalysisAdmin(admin.ModelAdmin):
    list_display = ["user", "date_from", "date_to", "reading_count", "model_used", "requested_at"]
    list_filter = ["model_used", "requested_at", "user"]
    search_fields = ["user__username"]
    readonly_fields = ["requested_at", "analysis_text", "reading_count", "model_used"]
    date_hierarchy = "requested_at"

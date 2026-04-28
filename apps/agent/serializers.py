from rest_framework import serializers

from .models import AgentAnalysis


class AgentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentAnalysis
        fields = [
            "id",
            "requested_at",
            "date_from",
            "date_to",
            "reading_count",
            "analysis_text",
            "model_used",
        ]
        read_only_fields = [
            "id",
            "requested_at",
            "reading_count",
            "analysis_text",
            "model_used",
        ]


class AnalysisRequestSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()

    def validate(self, data: dict) -> dict:
        if data["date_from"] > data["date_to"]:
            raise serializers.ValidationError(
                "La fecha de inicio no puede ser posterior a la fecha de fin."
            )
        return data

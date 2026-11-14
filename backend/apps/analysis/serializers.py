"""Analysis serializers."""

import hashlib

from django.conf import settings
from rest_framework import serializers

from .models import AnalysisJob, AnalysisResult


class SubmitAnalysisSerializer(serializers.Serializer):
    ciphertext = serializers.CharField(min_length=1, max_length=50000)

    def validate_ciphertext(self, value):
        max_len = settings.CIPHERMIND.get("MAX_CIPHERTEXT_LENGTH", 50000)
        if len(value) > max_len:
            raise serializers.ValidationError(f"Ciphertext exceeds {max_len} character limit.")
        return value


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = (
            "id", "candidates", "detected_encodings", "statistical_summary",
            "multilayer_chains", "ai_explanation", "processing_time_ms", "created_at",
        )


class AnalysisJobSerializer(serializers.ModelSerializer):
    result = AnalysisResultSerializer(read_only=True)
    ciphertext_preview = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisJob
        fields = (
            "id", "ciphertext_preview", "status", "created_at", "updated_at",
            "error_message", "result",
        )
        read_only_fields = fields

    def get_ciphertext_preview(self, obj) -> str:
        return obj.ciphertext[:100] + ("..." if len(obj.ciphertext) > 100 else "")

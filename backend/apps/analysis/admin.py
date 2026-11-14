from django.contrib import admin

from .models import AnalysisJob, AnalysisResult


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "ciphertext_preview")
    list_filter = ("status",)
    search_fields = ("user__email", "id")
    readonly_fields = ("id", "created_at", "updated_at", "celery_task_id", "ciphertext_hash")

    def ciphertext_preview(self, obj):
        return obj.ciphertext[:50]


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "processing_time_ms", "created_at")
    readonly_fields = ("id", "created_at")

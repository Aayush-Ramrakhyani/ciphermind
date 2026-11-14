"""
/*
 * Analysis models:
 *   AnalysisJob — tracks async analysis request lifecycle
 *   AnalysisResult — stores final ranked candidates and AI explanation
 *
 * IDOR prevention: all queries filter by request.user to prevent
 * cross-user data access.
 */
"""

import uuid

from django.conf import settings
from django.db import models


class AnalysisJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_DONE, "Done"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analysis_jobs",
    )
    ciphertext = models.TextField()
    ciphertext_hash = models.CharField(max_length=64, db_index=True)  # SHA-256 for dedup
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    celery_task_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "analysis_job"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["ciphertext_hash"]),
        ]

    def __str__(self) -> str:
        return f"Job {self.id} ({self.status})"


class AnalysisResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(AnalysisJob, on_delete=models.CASCADE, related_name="result")
    candidates = models.JSONField(default=list)
    detected_encodings = models.JSONField(default=list)
    statistical_summary = models.JSONField(default=dict)
    multilayer_chains = models.JSONField(default=list)
    ai_explanation = models.TextField(blank=True, null=True)
    processing_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analysis_result"

    def __str__(self) -> str:
        return f"Result for job {self.job_id}"

"""
/*
 * Analysis API views.
 * IDOR prevention: all querysets filter by request.user.
 * Rate limiting applied per-user via DRF throttling.
 */
"""

import hashlib

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalysisJob, AnalysisResult
from .serializers import AnalysisJobSerializer, SubmitAnalysisSerializer
from .tasks import run_analysis


class SubmitAnalysisView(APIView):
    """POST /api/v1/analysis/ — submit a new analysis job."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubmitAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ciphertext = serializer.validated_data["ciphertext"]
        ciphertext_hash = hashlib.sha256(ciphertext.encode()).hexdigest()

        # Check for recent identical analysis by this user (dedup within 1h)
        from django.utils import timezone
        from datetime import timedelta
        recent_job = (
            AnalysisJob.objects.filter(
                user=request.user,
                ciphertext_hash=ciphertext_hash,
                status=AnalysisJob.STATUS_DONE,
                created_at__gte=timezone.now() - timedelta(hours=1),
            )
            .order_by("-created_at")
            .first()
        )
        if recent_job:
            return Response(
                AnalysisJobSerializer(recent_job).data,
                status=status.HTTP_200_OK,
            )

        # Check active job count (prevent flooding)
        max_concurrent = settings.CIPHERMIND.get("MAX_CONCURRENT_ANALYSES", 5)
        active_count = AnalysisJob.objects.filter(
            user=request.user,
            status__in=[AnalysisJob.STATUS_PENDING, AnalysisJob.STATUS_RUNNING],
        ).count()
        if active_count >= max_concurrent:
            return Response(
                {"error": {"detail": "Too many active analysis jobs. Please wait."}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        job = AnalysisJob.objects.create(
            user=request.user,
            ciphertext=ciphertext,
            ciphertext_hash=ciphertext_hash,
            status=AnalysisJob.STATUS_PENDING,
        )
        run_analysis.delay(str(job.id))
        return Response(AnalysisJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class AnalysisJobListView(generics.ListAPIView):
    """GET /api/v1/analysis/ — list user's analysis jobs."""
    serializer_class = AnalysisJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # IDOR prevention: always filter by authenticated user
        return AnalysisJob.objects.filter(user=self.request.user).select_related("result")


class AnalysisJobDetailView(generics.RetrieveAPIView):
    """GET /api/v1/analysis/<uuid:pk>/ — get job status/result."""
    serializer_class = AnalysisJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # IDOR prevention: always filter by authenticated user
        return AnalysisJob.objects.filter(user=self.request.user).select_related("result")


class PlaygroundView(APIView):
    """POST /api/v1/playground/ — synchronous analysis for the interactive playground.

    No persistence — just runs the engine and returns inline.
    Limited to 1000 characters to keep latency acceptable.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from cryptanalysis.orchestrator import CryptanalysisOrchestrator

        ciphertext = request.data.get("ciphertext", "")
        if not ciphertext:
            return Response({"error": {"detail": "ciphertext is required."}}, status=status.HTTP_400_BAD_REQUEST)
        if len(ciphertext) > 1000:
            return Response(
                {"error": {"detail": "Playground limited to 1000 characters. Use /analysis/ for longer texts."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        orchestrator = CryptanalysisOrchestrator()
        result = orchestrator.analyse(ciphertext)
        return Response(result.to_dict())

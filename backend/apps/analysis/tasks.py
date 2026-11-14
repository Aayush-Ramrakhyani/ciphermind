"""
/*
 * Celery tasks for async cryptanalysis.
 * Runs the full CryptanalysisOrchestrator + AI enrichment in a worker process.
 */
"""

import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1, soft_time_limit=120, time_limit=150)
def run_analysis(self, job_id: str) -> None:
    """Execute full cryptanalysis pipeline for a given job ID."""
    from apps.analysis.models import AnalysisJob, AnalysisResult as AnalysisResultModel
    from ai.orchestrator import AIOrchestrator
    from ai.provider import get_provider
    from cryptanalysis.orchestrator import CryptanalysisOrchestrator

    try:
        job = AnalysisJob.objects.get(id=job_id)
        job.status = AnalysisJob.STATUS_RUNNING
        job.celery_task_id = self.request.id
        job.save(update_fields=["status", "celery_task_id"])

        # Run cryptanalysis
        crypto_settings = settings.CIPHERMIND
        orchestrator = CryptanalysisOrchestrator(settings=crypto_settings)
        analysis = orchestrator.analyse(job.ciphertext)

        # Enrich with AI if available
        ai_provider = get_provider(crypto_settings)
        ai_orch = AIOrchestrator(ai_provider)
        analysis = ai_orch.enrich(analysis)

        # Persist result
        AnalysisResultModel.objects.create(
            job=job,
            candidates=[c.to_dict() for c in analysis.candidates],
            detected_encodings=analysis.detected_encodings,
            statistical_summary=analysis.statistical_summary,
            multilayer_chains=analysis.multilayer_chains,
            ai_explanation=analysis.ai_explanation or "",
            processing_time_ms=analysis.processing_time_ms,
        )

        # Update user stats
        job.user.total_analyses += 1
        job.user.save(update_fields=["total_analyses"])

        job.status = AnalysisJob.STATUS_DONE
        job.save(update_fields=["status"])

    except AnalysisJob.DoesNotExist:
        logger.error("AnalysisJob %s not found", job_id)
    except Exception as exc:
        logger.exception("Analysis task failed for job %s: %s", job_id, exc)
        try:
            job = AnalysisJob.objects.get(id=job_id)
            job.status = AnalysisJob.STATUS_FAILED
            job.error_message = str(exc)[:500]
            job.save(update_fields=["status", "error_message"])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=5)

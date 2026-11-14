"""
/*
 * AI Orchestrator — bridges the cryptanalysis engine and the AI provider.
 * Enriches an AnalysisResult with an AI-generated explanation if available.
 */
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from cryptanalysis.base import AnalysisResult

logger = logging.getLogger(__name__)


class AIOrchestrator:
    def __init__(self, provider):
        self._provider = provider

    @property
    def ai_available(self) -> bool:
        return self._provider.is_available()

    def enrich(self, result: AnalysisResult) -> AnalysisResult:
        """Attach AI explanation to result in-place. Returns result."""
        if not self._provider.is_available():
            return result

        # Only send top-3 candidates to the AI to keep the prompt concise
        slim_dict = {
            "ciphertext_preview": result.ciphertext[:200],
            "statistical_summary": result.statistical_summary,
            "top_candidates": [c.to_dict() for c in result.candidates[:3]],
            "multilayer_chains": result.multilayer_chains[:2],
        }

        try:
            explanation = self._provider.explain_analysis(slim_dict)
            result.ai_explanation = explanation
        except Exception as exc:
            logger.warning("AI enrichment failed: %s", exc)

        return result

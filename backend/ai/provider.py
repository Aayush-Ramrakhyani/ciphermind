"""
/*
 * AI Provider abstraction layer.
 * CipherMind works fully without an API key — the AI layer is optional.
 * When a key is configured, the Anthropic provider enriches results with
 * reasoning explanations. Provider selection is driven by settings.
 */
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseAIProvider:
    """Null object — used when no API key is configured."""

    name: str = "none"
    available: bool = False

    def explain_analysis(self, analysis_dict: Dict[str, Any]) -> Optional[str]:
        return None

    def is_available(self) -> bool:
        return False


def get_provider(settings: Dict[str, Any]) -> BaseAIProvider:
    """Factory: return the appropriate AI provider based on settings."""
    api_key = settings.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            from ai.providers.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(
                api_key=api_key,
                model=settings.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            )
            logger.info("AI provider: Anthropic (%s)", provider.model)
            return provider
        except ImportError as exc:
            logger.error("Anthropic SDK not installed: %s", exc)

    logger.info("AI provider: none (no API key configured — cryptanalysis-only mode)")
    return BaseAIProvider()

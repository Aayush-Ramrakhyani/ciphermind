"""
/*
 * Anthropic Claude provider for CipherMind AI explanations.
 * Uses claude-opus-4-8 with adaptive thinking and streaming for
 * long cryptanalysis explanations.
 */
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import anthropic

from ai.provider import BaseAIProvider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are CipherMind's expert cryptanalysis reasoning engine.
You receive a JSON object containing:
- The original ciphertext
- Statistical measurements (IoC, chi-squared, bigram log-probability, letter frequencies)
- A ranked list of candidate decryptions with cipher types, keys, and confidence levels
- Multi-layer transformation chains (if found)

Your task is to:
1. Explain WHY each top candidate makes cryptographic sense based on the statistics
2. Identify which cipher family the ciphertext most likely belongs to and explain the evidence
3. Describe the mathematical reasoning (e.g. IoC 0.065 ≈ monoalphabetic shift cipher)
4. Flag any anomalies or reasons to doubt the top candidate
5. Recommend next steps if confidence is low

Write for a technically-literate audience. Be precise about mathematics.
Do not guess — base every claim on the data provided.
Respond in clear paragraphs, no more than 500 words."""


class AnthropicProvider(BaseAIProvider):
    """Claude-powered cryptanalysis explanation provider."""

    name = "anthropic"
    available = True

    def __init__(self, api_key: str, model: str = "claude-opus-4-8"):
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def is_available(self) -> bool:
        return True

    def explain_analysis(self, analysis_dict: Dict[str, Any]) -> Optional[str]:
        """Stream an AI explanation for the analysis result."""
        try:
            payload = json.dumps(analysis_dict, indent=2)[:8000]  # stay within context

            # Use streaming with adaptive thinking for complex reasoning
            full_text = ""
            with self._client.messages.stream(
                model=self.model,
                max_tokens=1024,
                thinking={"type": "adaptive"},
                system=_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Analyse this cryptanalysis result and explain your reasoning:\n\n{payload}",
                    }
                ],
            ) as stream:
                for event in stream:
                    if hasattr(event, "type"):
                        if event.type == "content_block_delta":
                            delta = getattr(event.delta, "text", "")
                            if delta:
                                full_text += delta

            return full_text.strip() if full_text.strip() else None

        except anthropic.AuthenticationError:
            logger.error("Anthropic API key is invalid")
            return None
        except anthropic.RateLimitError:
            logger.warning("Anthropic rate limit hit")
            return None
        except Exception as exc:
            logger.error("Anthropic provider error: %s", exc)
            return None

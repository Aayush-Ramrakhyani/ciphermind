"""
/*
 * Multi-layer transformation search engine.
 * Uses a bounded DFS/BFS to explore chains of decodings/decryptions
 * up to MAX_DEPTH layers deep.  Prunes branches whose intermediate
 * language score falls below a minimum threshold.
 *
 * Example chain: Base64 → Caesar → plaintext
 */
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from cryptanalysis.base import CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

logger = logging.getLogger(__name__)

MAX_DEPTH = 3
MIN_INTERMEDIATE_SCORE = 0.10  # prune branches with worse intermediate scores


@dataclass
class TransformNode:
    """One step in a transformation chain."""
    transform_name: str
    input_text: str
    output_text: str
    key: Any
    score: float


@dataclass
class TransformChain:
    """A complete chain of transformations from ciphertext to plaintext."""
    steps: List[TransformNode] = field(default_factory=list)
    final_score: float = 0.0
    confidence: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "transform": s.transform_name,
                    "key": s.key if isinstance(s.key, (str, int, list)) else str(s.key),
                    "output_preview": s.output_text[:100],
                    "score": round(s.score, 4),
                }
                for s in self.steps
            ],
            "final_score": round(self.final_score, 4),
            "confidence": self.confidence,
            "plaintext": self.steps[-1].output_text if self.steps else "",
        }


# Type alias for a transformation function: takes text, returns list of (name, key, output)
TransformFn = Callable[[str], List[Tuple[str, Any, str]]]


class MultiLayerSearchEngine:
    """DFS search over transformation chains."""

    def __init__(
        self,
        transforms: List[TransformFn],
        max_depth: int = MAX_DEPTH,
        min_intermediate_score: float = MIN_INTERMEDIATE_SCORE,
        top_n: int = 5,
    ):
        self.transforms = transforms
        self.max_depth = max_depth
        self.min_intermediate_score = min_intermediate_score
        self.top_n = top_n

    def search(self, ciphertext: str) -> List[TransformChain]:
        """Return best multi-layer chains, sorted by final score descending."""
        chains: List[TransformChain] = []
        self._dfs(ciphertext, [], chains)
        chains.sort(key=lambda c: -c.final_score)
        return chains[: self.top_n]

    def _dfs(
        self,
        current_text: str,
        path: List[TransformNode],
        results: List[TransformChain],
    ) -> None:
        depth = len(path)

        # Only record multi-step chains (depth >= 2 means at least one transform applied)
        if depth >= 2:
            final_score = score_text(current_text)
            if final_score >= self.min_intermediate_score:
                confidence = classify_confidence(final_score)
                chain = TransformChain(
                    steps=list(path),
                    final_score=final_score,
                    confidence=confidence,
                )
                results.append(chain)

        if depth >= self.max_depth:
            return

        for transform_fn in self.transforms:
            try:
                variants = transform_fn(current_text)
            except Exception as exc:
                logger.debug("Transform error at depth %d: %s", depth, exc)
                continue

            for name, key, output in variants:
                if not output or output == current_text:
                    continue
                intermediate_score = score_text(output)
                if intermediate_score < self.min_intermediate_score and depth > 0:
                    continue  # prune
                node = TransformNode(
                    transform_name=name,
                    input_text=current_text,
                    output_text=output,
                    key=key,
                    score=intermediate_score,
                )
                self._dfs(output, path + [node], results)

"""
/*
 * CipherMind Cryptanalysis Base
 * Defines the shared data structures and abstract solver interface used
 * by every cipher, encoding, and statistical module.
 */
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"        # IoC/chi² strongly matches English + passes word-frequency check
    LIKELY = "likely"    # Reasonable language score but not conclusive
    POSSIBLE = "possible"  # Statistical signal present, but weak
    NONE = "none"        # No reliable solution found


@dataclass
class CipherCandidate:
    """A single decryption hypothesis produced by a solver."""

    cipher_type: str                      # e.g. "caesar", "vigenere"
    plaintext: str                        # recovered plaintext
    key: Any                              # key used (shift int, keyword str, dict, …)
    confidence: ConfidenceLevel
    language_score: float                 # higher is better (log-prob or chi² inverse)
    explanation: str                      # human-readable reasoning
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cipher_type": self.cipher_type,
            "plaintext": self.plaintext,
            "key": self.key if isinstance(self.key, (str, int, float, list)) else str(self.key),
            "confidence": self.confidence.value,
            "language_score": round(self.language_score, 4),
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass
class AnalysisResult:
    """Full result returned by the orchestrator for one ciphertext."""

    ciphertext: str
    candidates: List[CipherCandidate] = field(default_factory=list)
    detected_encodings: List[str] = field(default_factory=list)
    statistical_summary: Dict[str, Any] = field(default_factory=dict)
    multilayer_chains: List[Dict[str, Any]] = field(default_factory=list)
    ai_explanation: Optional[str] = None
    processing_time_ms: int = 0

    def top_candidate(self) -> Optional[CipherCandidate]:
        return self.candidates[0] if self.candidates else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ciphertext": self.ciphertext,
            "candidates": [c.to_dict() for c in self.candidates],
            "detected_encodings": self.detected_encodings,
            "statistical_summary": self.statistical_summary,
            "multilayer_chains": self.multilayer_chains,
            "ai_explanation": self.ai_explanation,
            "processing_time_ms": self.processing_time_ms,
        }


class BaseSolver:
    """Abstract interface that every cipher/encoding solver must implement."""

    name: str = "unknown"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        """Return a list of decryption candidates, best first."""
        raise NotImplementedError

    def can_handle(self, ciphertext: str) -> bool:
        """Fast pre-check: return False to skip this solver entirely."""
        return True

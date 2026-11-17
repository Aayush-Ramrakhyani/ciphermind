"""
/*
 * Binary encoding detector and decoder.
 * Accepts space-separated 8-bit groups or a continuous binary string.
 */
"""

from __future__ import annotations

import re
from typing import List, Optional

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

_BINARY_SPACED = re.compile(r"^[01]{8}(\s[01]{8})*$")
_BINARY_CONTINUOUS = re.compile(r"^[01]+$")


def _try_decode_spaced(text: str) -> Optional[str]:
    groups = text.strip().split()
    if not all(len(g) == 8 and set(g) <= {"0", "1"} for g in groups):
        return None
    try:
        chars = [chr(int(g, 2)) for g in groups]
        return "".join(chars)
    except Exception:
        return None


def _try_decode_continuous(text: str) -> Optional[str]:
    text = text.strip()
    if len(text) % 8 != 0:
        return None
    try:
        chars = [chr(int(text[i : i + 8], 2)) for i in range(0, len(text), 8)]
        return "".join(chars)
    except Exception:
        return None


class BinarySolver(BaseSolver):
    name = "binary"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        decoded = _try_decode_spaced(ciphertext)
        method = "space-separated 8-bit groups"
        if decoded is None:
            decoded = _try_decode_continuous(ciphertext)
            method = "continuous binary string"
        if decoded is None:
            return []

        sc = score_text(decoded)
        content_confidence = ConfidenceLevel(classify_confidence(sc))
        if content_confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.HIGH
        elif sc > 0.05:
            confidence = ConfidenceLevel.LIKELY
        else:
            confidence = content_confidence
        return [
            CipherCandidate(
                cipher_type="binary",
                plaintext=decoded,
                key="binary",
                confidence=confidence,
                language_score=sc,
                explanation=f"Decoded from binary encoding ({method}) — structural detection confirmed",
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        text = ciphertext.strip()
        return bool(_BINARY_SPACED.match(text)) or (
            bool(_BINARY_CONTINUOUS.match(text)) and len(text) >= 8 and len(text) % 8 == 0
        )

"""
/*
 * Base64 / Base64URL encoding detector and decoder.
 * Detects standard Base64, URL-safe Base64, and Base64 without padding.
 */
"""

from __future__ import annotations

import base64
import re
from typing import List, Optional

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

_B64_PATTERN = re.compile(r"^[A-Za-z0-9+/\-_]+={0,2}$")


def _try_decode(text: str) -> Optional[str]:
    text = text.strip()
    # Normalise URL-safe chars
    normalised = text.replace("-", "+").replace("_", "/")
    # Add padding if needed
    pad = 4 - len(normalised) % 4
    if pad != 4:
        normalised += "=" * pad
    try:
        decoded_bytes = base64.b64decode(normalised, validate=True)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        return None


class Base64Solver(BaseSolver):
    name = "base64"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        decoded = _try_decode(ciphertext.strip())
        if decoded is None:
            return []
        sc = score_text(decoded)
        content_confidence = ConfidenceLevel(classify_confidence(sc))
        # Structural detection (regex match + clean decode) guarantees at least LIKELY.
        # This prevents cipher solvers that accidentally score higher from outranking
        # a confirmed encoding detection.
        if content_confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.HIGH
        else:
            confidence = ConfidenceLevel.LIKELY
        return [
            CipherCandidate(
                cipher_type="base64",
                plaintext=decoded,
                key="base64",
                confidence=confidence,
                language_score=sc,
                explanation="Decoded from Base64 / Base64URL encoding (structural detection confirmed)",
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        text = ciphertext.strip()
        return bool(_B64_PATTERN.match(text)) and len(text) >= 4

"""
/*
 * Hexadecimal encoding detector and decoder.
 * Handles lowercase, uppercase, and 0x-prefixed hex strings.
 */
"""

from __future__ import annotations

import re
from typing import List, Optional

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

_HEX_PATTERN = re.compile(r"^(?:0x)?[0-9A-Fa-f\s]+$")


def _try_decode(text: str) -> Optional[str]:
    # Strip 0x prefix and whitespace
    cleaned = re.sub(r"\s+", "", text.strip())
    cleaned = cleaned.lstrip("0x").lstrip("0X")
    if len(cleaned) % 2 != 0:
        return None
    try:
        decoded_bytes = bytes.fromhex(cleaned)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        return None


class HexSolver(BaseSolver):
    name = "hex"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        decoded = _try_decode(ciphertext)
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
                cipher_type="hex",
                plaintext=decoded,
                key="hex",
                confidence=confidence,
                language_score=sc,
                explanation="Decoded from hexadecimal encoding (structural detection confirmed)",
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        cleaned = re.sub(r"\s+", "", ciphertext.strip())
        cleaned = cleaned.lstrip("0x").lstrip("0X")
        return bool(_HEX_PATTERN.match(ciphertext.strip())) and len(cleaned) >= 2 and len(cleaned) % 2 == 0

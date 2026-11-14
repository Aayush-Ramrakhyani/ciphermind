"""
/*
 * Atbash cipher solver.
 * Atbash maps A↔Z, B↔Y, C↔X, etc. — it is its own inverse.
 */
"""

from __future__ import annotations

from typing import List

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text


def atbash_decrypt(text: str) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            if ch.isupper():
                result.append(chr(ord("Z") - (ord(ch) - ord("A"))))
            else:
                result.append(chr(ord("z") - (ord(ch) - ord("a"))))
        else:
            result.append(ch)
    return "".join(result)


class AtbashSolver(BaseSolver):
    name = "atbash"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        plaintext = atbash_decrypt(ciphertext)
        sc = score_text(plaintext)
        confidence = ConfidenceLevel(classify_confidence(sc))
        return [
            CipherCandidate(
                cipher_type="atbash",
                plaintext=plaintext,
                key="atbash",
                confidence=confidence,
                language_score=sc,
                explanation="Atbash reversal: A↔Z, B↔Y, … (self-inverse cipher)",
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        return sum(1 for c in ciphertext if c.isalpha()) >= 4

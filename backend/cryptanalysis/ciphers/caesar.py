"""
/*
 * Caesar / ROT cipher solver.
 * Brute-forces all 26 shifts, scores each decryption with the language
 * scorer, and returns ranked candidates.
 */
"""

from __future__ import annotations

from typing import List

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text


def _caesar_decrypt(ciphertext: str, shift: int) -> str:
    result = []
    for ch in ciphertext:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base - shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


class CaesarSolver(BaseSolver):
    name = "caesar"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        candidates = []
        for shift in range(26):
            plaintext = _caesar_decrypt(ciphertext, shift)
            sc = score_text(plaintext)
            confidence = ConfidenceLevel(classify_confidence(sc))
            candidates.append(
                CipherCandidate(
                    cipher_type="caesar",
                    plaintext=plaintext,
                    key=shift,
                    confidence=confidence,
                    language_score=sc,
                    explanation=f"Caesar shift {shift}: decrypted with ROT-{shift}",
                )
            )
        # Sort best score first; skip shift=0 (identity) unless it's genuinely best
        candidates.sort(key=lambda c: -c.language_score)
        # Return top 3 non-trivial candidates plus shift 0 if it scored high
        top = [c for c in candidates if c.key != 0][:3]
        identity = next((c for c in candidates if c.key == 0), None)
        if identity and identity.language_score >= 0.60:
            top = [identity] + top
        return top[:5]

    def can_handle(self, ciphertext: str) -> bool:
        # Need at least some alphabetic content
        alpha = sum(1 for c in ciphertext if c.isalpha())
        return alpha >= 4

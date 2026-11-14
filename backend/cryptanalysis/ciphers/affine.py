"""
/*
 * Affine cipher solver.
 * E(x) = (a·x + b) mod 26.  Brute-forces all 312 valid (a, b) combinations.
 * Valid 'a' values: those coprime to 26 → {1,3,5,7,9,11,15,17,19,21,23,25}.
 */
"""

from __future__ import annotations

from typing import List, Optional

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

_VALID_A = [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25]


def _mod_inverse(a: int, m: int) -> Optional[int]:
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return None


# Precompute inverses
_INV_A = {a: _mod_inverse(a, 26) for a in _VALID_A}


def affine_decrypt(ciphertext: str, a: int, b: int) -> Optional[str]:
    a_inv = _INV_A.get(a)
    if a_inv is None:
        return None
    result = []
    for ch in ciphertext:
        if ch.isalpha():
            x = ord(ch.lower()) - ord("a")
            decrypted = (a_inv * (x - b)) % 26
            letter = chr(decrypted + ord("a"))
            result.append(letter.upper() if ch.isupper() else letter)
        else:
            result.append(ch)
    return "".join(result)


class AffineSolver(BaseSolver):
    name = "affine"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        candidates = []
        for a in _VALID_A:
            for b in range(26):
                plaintext = affine_decrypt(ciphertext, a, b)
                if plaintext is None:
                    continue
                sc = score_text(plaintext)
                confidence = ConfidenceLevel(classify_confidence(sc))
                if confidence != ConfidenceLevel.NONE:
                    candidates.append(
                        CipherCandidate(
                            cipher_type="affine",
                            plaintext=plaintext,
                            key={"a": a, "b": b},
                            confidence=confidence,
                            language_score=sc,
                            explanation=f"Affine cipher: a={a}, b={b} — E(x)=({a}x+{b}) mod 26",
                        )
                    )
        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:5]

    def can_handle(self, ciphertext: str) -> bool:
        return sum(1 for c in ciphertext if c.isalpha()) >= 6

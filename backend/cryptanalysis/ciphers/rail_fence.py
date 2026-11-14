"""
/*
 * Rail Fence (zigzag) transposition cipher solver.
 * Brute-forces rail counts 2–12 and scores each decryption.
 */
"""

from __future__ import annotations

from typing import List

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text


def rail_fence_decrypt(ciphertext: str, num_rails: int) -> str:
    """Reconstruct plaintext from rail-fence ciphertext."""
    n = len(ciphertext)
    if num_rails == 1 or num_rails >= n:
        return ciphertext

    # Build rail pattern indices
    rails = [[] for _ in range(num_rails)]
    rail = 0
    direction = 1
    for i in range(n):
        rails[rail].append(i)
        if rail == 0:
            direction = 1
        elif rail == num_rails - 1:
            direction = -1
        rail += direction

    # Assign characters to rails in order
    result = [""] * n
    idx = 0
    for r in range(num_rails):
        for pos in rails[r]:
            result[pos] = ciphertext[idx]
            idx += 1
    return "".join(result)


class RailFenceSolver(BaseSolver):
    name = "rail_fence"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        candidates = []
        max_rails = min(12, len(ciphertext) // 2 + 1)
        for rails in range(2, max_rails + 1):
            plaintext = rail_fence_decrypt(ciphertext, rails)
            sc = score_text(plaintext)
            confidence = ConfidenceLevel(classify_confidence(sc))
            if confidence != ConfidenceLevel.NONE:
                candidates.append(
                    CipherCandidate(
                        cipher_type="rail_fence",
                        plaintext=plaintext,
                        key=rails,
                        confidence=confidence,
                        language_score=sc,
                        explanation=f"Rail Fence with {rails} rails (zigzag transposition)",
                        metadata={"num_rails": rails},
                    )
                )
        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:3]

    def can_handle(self, ciphertext: str) -> bool:
        return len(ciphertext) >= 4

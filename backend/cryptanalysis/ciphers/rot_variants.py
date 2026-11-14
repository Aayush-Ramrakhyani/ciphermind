"""
/*
 * ROT-N variant solver (ROT5 for digits, ROT13, ROT18, ROT47).
 * Extends the basic Caesar logic to cover common ROT-family ciphers.
 */
"""

from __future__ import annotations

from typing import List

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text


def rot13(text: str) -> str:
    """Standard ROT13 substitution."""
    result = []
    for ch in text:
        if "a" <= ch <= "z":
            result.append(chr((ord(ch) - ord("a") + 13) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            result.append(chr((ord(ch) - ord("A") + 13) % 26 + ord("A")))
        else:
            result.append(ch)
    return "".join(result)


def rot5(text: str) -> str:
    """ROT5: rotate digits 0-9 by 5."""
    result = []
    for ch in text:
        if "0" <= ch <= "9":
            result.append(chr((ord(ch) - ord("0") + 5) % 10 + ord("0")))
        else:
            result.append(ch)
    return "".join(result)


def rot18(text: str) -> str:
    """ROT18 = ROT13 on letters + ROT5 on digits."""
    return rot5(rot13(text))


def rot47(text: str) -> str:
    """ROT47: rotate printable ASCII characters 33–126."""
    result = []
    for ch in text:
        code = ord(ch)
        if 33 <= code <= 126:
            result.append(chr((code - 33 + 47) % 94 + 33))
        else:
            result.append(ch)
    return "".join(result)


class RotVariantsSolver(BaseSolver):
    name = "rot_variants"

    _VARIANTS = [
        ("rot13", rot13),
        ("rot5", rot5),
        ("rot18", rot18),
        ("rot47", rot47),
    ]

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        candidates = []
        for variant_name, fn in self._VARIANTS:
            plaintext = fn(ciphertext)
            sc = score_text(plaintext)
            confidence = ConfidenceLevel(classify_confidence(sc))
            if confidence != ConfidenceLevel.NONE:
                candidates.append(
                    CipherCandidate(
                        cipher_type=variant_name,
                        plaintext=plaintext,
                        key=variant_name,
                        confidence=confidence,
                        language_score=sc,
                        explanation=f"Applied {variant_name.upper()} transformation",
                    )
                )
        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:3]

    def can_handle(self, ciphertext: str) -> bool:
        return len(ciphertext) >= 2

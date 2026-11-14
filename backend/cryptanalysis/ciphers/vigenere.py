"""
/*
 * Vigenère cipher solver.
 * Key-length estimation: Kasiski test + IoC-per-column analysis.
 * Key recovery: frequency analysis on each column independently.
 * Scores each candidate key with the language scorer.
 */
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Optional, Tuple

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.frequency import ENGLISH_UNIGRAM_FREQ, chi_squared
from cryptanalysis.statistical.ioc import average_ioc_for_key_length, best_key_lengths
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text


def _vigenere_decrypt(ciphertext: str, key: str) -> str:
    key = key.lower()
    key_len = len(key)
    result = []
    key_idx = 0
    for ch in ciphertext:
        if ch.isalpha():
            shift = ord(key[key_idx % key_len]) - ord("a")
            decrypted = (ord(ch.lower()) - ord("a") - shift) % 26
            letter = chr(decrypted + ord("a"))
            result.append(letter.upper() if ch.isupper() else letter)
            key_idx += 1
        else:
            result.append(ch)
    return "".join(result)


def _kasiski_key_lengths(text: str, min_len: int = 3) -> List[int]:
    """Estimate key lengths from repeated trigram spacings (Kasiski test)."""
    text_clean = "".join(c.lower() for c in text if c.isalpha())
    spacings = []
    for seq_len in range(min_len, min(8, len(text_clean) // 3)):
        positions: Dict[str, int] = {}
        for i in range(len(text_clean) - seq_len + 1):
            seq = text_clean[i : i + seq_len]
            if seq in positions:
                spacings.append(i - positions[seq])
            else:
                positions[seq] = i

    if not spacings:
        return []

    gcd_counts: Counter = Counter()
    for s in spacings:
        for d in range(2, min(s + 1, 21)):
            if s % d == 0:
                gcd_counts[d] += 1

    return [k for k, _ in gcd_counts.most_common(10)]


def _recover_key_for_length(text: str, key_len: int) -> str:
    """Recover keyword by frequency-analysing each column (best single chi2 key)."""
    letters = [c.lower() for c in text if c.isalpha()]
    key_letters = []
    for col in range(key_len):
        column = letters[col::key_len]
        if not column:
            key_letters.append("a")
            continue
        best_shift = 0
        best_chi = math.inf
        col_text = "".join(column)
        for shift in range(26):
            shifted = "".join(chr((ord(c) - ord("a") - shift) % 26 + ord("a")) for c in col_text)
            chi2 = chi_squared(shifted)
            if chi2 < best_chi:
                best_chi = chi2
                best_shift = shift
        key_letters.append(chr(best_shift + ord("a")))
    return "".join(key_letters)


def _recover_key_candidates(text: str, key_len: int, top_per_col: int = 2) -> List[str]:
    """Return multiple key candidates by trying top-N chi2 shifts per column.

    For key_len <= 6, top_per_col=2 gives 2^key_len candidates — feasible.
    For longer keys we fall back to single-shift recovery to avoid 2^N explosion.
    """
    import itertools as _it
    if key_len > 6:
        return [_recover_key_for_length(text, key_len)]

    letters = [c.lower() for c in text if c.isalpha()]
    col_top_shifts: List[List[int]] = []
    for col in range(key_len):
        column = letters[col::key_len]
        col_text = "".join(column)
        if not col_text:
            col_top_shifts.append([0])
            continue
        scored = []
        for shift in range(26):
            shifted = "".join(chr((ord(c) - ord("a") - shift) % 26 + ord("a")) for c in col_text)
            scored.append((shift, chi_squared(shifted)))
        scored.sort(key=lambda x: x[1])
        col_top_shifts.append([s for s, _ in scored[:top_per_col]])

    return [
        "".join(chr(s + ord("a")) for s in combo)
        for combo in _it.product(*col_top_shifts)
    ]


class VigenereSolver(BaseSolver):
    name = "vigenere"

    def __init__(self, max_key_len: int = 20):
        self.max_key_len = max_key_len

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        # Collect candidate key lengths from both methods
        kasiski_lengths = _kasiski_key_lengths(ciphertext)
        ioc_lengths = best_key_lengths(ciphertext, self.max_key_len)

        # Merge, deduplicate, limit
        seen = set()
        combined: List[int] = []
        for kl in kasiski_lengths + ioc_lengths:
            if kl not in seen and 2 <= kl <= self.max_key_len:
                seen.add(kl)
                combined.append(kl)
        candidate_lengths = combined[:8]  # test at most 8 lengths

        candidates = []
        seen_keys: set = set()
        for key_len in candidate_lengths:
            # Try top-2 shifts per column to handle noisy columns
            key_candidates = _recover_key_candidates(ciphertext, key_len, top_per_col=2)
            ioc = average_ioc_for_key_length(ciphertext, key_len)
            for keyword in key_candidates:
                if keyword in seen_keys:
                    continue
                seen_keys.add(keyword)
                plaintext = _vigenere_decrypt(ciphertext, keyword)
                sc = score_text(plaintext)
                confidence = ConfidenceLevel(classify_confidence(sc))
                candidates.append(
                    CipherCandidate(
                        cipher_type="vigenere",
                        plaintext=plaintext,
                        key=keyword,
                        confidence=confidence,
                        language_score=sc,
                        explanation=(
                            f"Vigenere key length {key_len} (keyword: '{keyword}'). "
                            f"Avg IoC per column: {ioc:.4f}. "
                            "Key recovered via per-column chi-squared minimisation."
                        ),
                        metadata={"key_length": key_len, "avg_ioc": round(ioc, 4)},
                    )
                )

        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:5]

    def can_handle(self, ciphertext: str) -> bool:
        return sum(1 for c in ciphertext if c.isalpha()) >= 15

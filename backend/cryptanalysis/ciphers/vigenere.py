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


def _refine_key(ciphertext: str, initial_key: str) -> Tuple[str, float]:
    """Hill-climb each key position to maximise language score."""
    key = list(initial_key)
    best_sc = score_text(_vigenere_decrypt(ciphertext, "".join(key)))
    improved = True
    while improved:
        improved = False
        for pos in range(len(key)):
            for shift in range(26):
                candidate = key[:]
                candidate[pos] = chr(shift + ord("a"))
                sc = score_text(_vigenere_decrypt(ciphertext, "".join(candidate)))
                if sc > best_sc:
                    best_sc = sc
                    key[pos] = chr(shift + ord("a"))
                    improved = True
    return "".join(key), best_sc


class VigenereSolver(BaseSolver):
    name = "vigenere"

    def __init__(self, max_key_len: int = 20):
        self.max_key_len = max_key_len

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        # Collect and merge candidate key lengths, cap at 6 to limit search space
        seen: set = set()
        combined: List[int] = []
        for kl in _kasiski_key_lengths(ciphertext) + best_key_lengths(ciphertext, self.max_key_len):
            if kl not in seen and 2 <= kl <= self.max_key_len:
                seen.add(kl)
                combined.append(kl)
        candidate_lengths = combined[:6]

        # Phase 1: quick initial score for each key length (single best key, no hill-climb)
        initial: List[Tuple[str, float, int]] = []
        seen_keys: set = set()
        for key_len in candidate_lengths:
            keyword = _recover_key_for_length(ciphertext, key_len)
            if keyword in seen_keys:
                continue
            seen_keys.add(keyword)
            sc = score_text(_vigenere_decrypt(ciphertext, keyword))
            initial.append((keyword, sc, key_len))

        # Phase 2: hill-climb only the top 3 initial candidates
        initial.sort(key=lambda x: -x[1])
        candidates = []
        seen_refined: set = set()
        for keyword, _, key_len in initial[:3]:
            ioc = average_ioc_for_key_length(ciphertext, key_len)
            refined_key, sc = _refine_key(ciphertext, keyword)
            if refined_key in seen_refined:
                continue
            seen_refined.add(refined_key)
            penalised_sc = round(sc - 0.008 * len(refined_key), 4)
            candidates.append(
                CipherCandidate(
                    cipher_type="vigenere",
                    plaintext=_vigenere_decrypt(ciphertext, refined_key),
                    key=refined_key,
                    confidence=ConfidenceLevel(classify_confidence(penalised_sc)),
                    language_score=penalised_sc,
                    explanation=(
                        f"Vigenere key length {key_len} (keyword: '{refined_key}'). "
                        f"Avg IoC per column: {ioc:.4f}. "
                        "Key recovered via chi-squared + hill-climb refinement."
                    ),
                    metadata={"key_length": key_len, "avg_ioc": round(ioc, 4)},
                )
            )

        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:3]

    def can_handle(self, ciphertext: str) -> bool:
        return sum(1 for c in ciphertext if c.isalpha()) >= 15

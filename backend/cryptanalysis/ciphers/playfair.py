"""
/*
 * Playfair cipher solver via simulated annealing on the 5×5 key square.
 * Fitness function: bigram log-probability on the decrypted digraphs.
 * This is computationally intensive — limited iterations are used by default.
 */
"""

from __future__ import annotations

import math
import random
import string
from typing import List, Optional, Tuple

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text
from cryptanalysis.statistical.ngram import bigram_log_probability


_ALPHABET_NO_J = "ABCDEFGHIKLMNOPQRSTUVWXYZ"  # J merged with I in Playfair


def _build_square(keyword: str) -> List[List[str]]:
    keyword = keyword.upper().replace("J", "I")
    seen = set()
    ordered = []
    for ch in keyword + _ALPHABET_NO_J:
        if ch not in seen and ch.isalpha():
            seen.add(ch)
            ordered.append(ch)
    return [ordered[i * 5 : i * 5 + 5] for i in range(5)]


def _square_to_index(square: List[List[str]]) -> dict:
    idx = {}
    for r, row in enumerate(square):
        for c, ch in enumerate(row):
            idx[ch] = (r, c)
    return idx


def _playfair_decrypt_digraph(a: str, b: str, square: List[List[str]], idx: dict) -> Tuple[str, str]:
    r1, c1 = idx[a]
    r2, c2 = idx[b]
    if r1 == r2:
        return square[r1][(c1 - 1) % 5], square[r2][(c2 - 1) % 5]
    elif c1 == c2:
        return square[(r1 - 1) % 5][c1], square[(r2 - 1) % 5][c2]
    else:
        return square[r1][c2], square[r2][c1]


def _playfair_decrypt(ciphertext: str, square: List[List[str]]) -> str:
    text = "".join(c.upper() for c in ciphertext if c.isalpha()).replace("J", "I")
    if len(text) % 2 != 0:
        text += "X"
    idx = _square_to_index(square)
    result = []
    for i in range(0, len(text), 2):
        a, b = text[i], text[i + 1]
        if a not in idx or b not in idx:
            result.extend([a, b])
            continue
        pa, pb = _playfair_decrypt_digraph(a, b, square, idx)
        result.extend([pa, pb])
    return "".join(result).lower()


def _swap_random(square: List[List[str]]) -> List[List[str]]:
    """Return a new square with two random cells swapped."""
    flat = [ch for row in square for ch in row]
    i, j = random.sample(range(25), 2)
    flat[i], flat[j] = flat[j], flat[i]
    return [flat[k * 5 : k * 5 + 5] for k in range(5)]


def _solve_playfair_sa(ciphertext: str, max_iter: int = 5000) -> Tuple[str, List[List[str]], float]:
    """Simulated annealing over the 5×5 Playfair key square."""
    # Random initial square
    chars = list(_ALPHABET_NO_J)
    random.shuffle(chars)
    square = [chars[i * 5 : i * 5 + 5] for i in range(5)]

    decrypted = _playfair_decrypt(ciphertext, square)
    best_score = bigram_log_probability(decrypted)
    best_square = [row[:] for row in square]
    best_text = decrypted

    for iteration in range(max_iter):
        new_square = _swap_random(square)
        new_text = _playfair_decrypt(ciphertext, new_square)
        new_score = bigram_log_probability(new_text)

        temp = max(0.5, 10.0 * math.exp(-3.0 * iteration / max_iter))
        delta = new_score - best_score
        if delta > 0 or random.random() < math.exp(delta / temp):
            square = new_square
            if new_score > best_score:
                best_score = new_score
                best_square = [row[:] for row in new_square]
                best_text = new_text

    return best_text, best_square, best_score


class PlayfairSolver(BaseSolver):
    name = "playfair"

    def __init__(self, max_iter: int = 5000):
        self.max_iter = max_iter

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        plaintext, square, _ = _solve_playfair_sa(ciphertext, self.max_iter)
        sc = score_text(plaintext)
        confidence = ConfidenceLevel(classify_confidence(sc))
        square_flat = "".join(ch for row in square for ch in row)
        return [
            CipherCandidate(
                cipher_type="playfair",
                plaintext=plaintext,
                key=square_flat,
                confidence=confidence,
                language_score=sc,
                explanation=(
                    f"Playfair cipher solved via simulated annealing ({self.max_iter} iterations). "
                    f"Recovered 5×5 key square: {square_flat}"
                ),
                metadata={"key_square": square_flat},
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        alpha = sum(1 for c in ciphertext if c.isalpha())
        # Playfair needs at least 30 alpha chars — SA is unreliable on short text
        # and would generate false positives that outrank correct simple ciphers.
        return alpha >= 30 and alpha % 2 == 0

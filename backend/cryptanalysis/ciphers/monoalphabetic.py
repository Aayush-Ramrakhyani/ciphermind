"""
/*
 * Monoalphabetic substitution cipher solver using simulated annealing.
 * Initial key estimated via frequency analysis; hill-climbing then optimises
 * by randomly swapping pairs of key letters and accepting improvements.
 * Uses bigram log-probability as the fitness function.
 */
"""

from __future__ import annotations

import math
import random
import string
from typing import Dict, List, Tuple

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.frequency import ENGLISH_UNIGRAM_FREQ, letter_frequencies
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text
from cryptanalysis.statistical.ngram import bigram_log_probability


_ALPHABET = string.ascii_lowercase


def _apply_key(ciphertext: str, key: Dict[str, str]) -> str:
    result = []
    for ch in ciphertext:
        lower = ch.lower()
        mapped = key.get(lower, lower)
        result.append(mapped.upper() if ch.isupper() else mapped)
    return "".join(result)


def _initial_key_from_frequency(ciphertext: str) -> Dict[str, str]:
    """Build an initial substitution key by matching cipher letter frequencies
    to expected English letter frequencies."""
    cipher_freq = letter_frequencies(ciphertext)
    sorted_cipher = sorted(_ALPHABET, key=lambda c: -cipher_freq.get(c, 0))
    sorted_english = sorted(_ALPHABET, key=lambda c: -ENGLISH_UNIGRAM_FREQ.get(c, 0))
    return dict(zip(sorted_cipher, sorted_english))


def solve_with_hill_climbing(
    ciphertext: str,
    max_iterations: int = 10000,
    restarts: int = 3,
) -> Tuple[str, Dict[str, str], float]:
    """Return (best_plaintext, best_key, best_score)."""
    best_overall_score = -math.inf
    best_overall_plaintext = ciphertext
    best_overall_key: Dict[str, str] = {c: c for c in _ALPHABET}

    for _ in range(restarts):
        key = _initial_key_from_frequency(ciphertext)
        # Add any missing letters
        used = set(key.values())
        remaining = [l for l in _ALPHABET if l not in used]
        for cipher_letter in _ALPHABET:
            if cipher_letter not in key:
                key[cipher_letter] = remaining.pop(0) if remaining else cipher_letter

        current_plaintext = _apply_key(ciphertext, key)
        current_score = bigram_log_probability(current_plaintext)

        for iteration in range(max_iterations):
            # Pick two random cipher letters to swap in the key
            a, b = random.sample(_ALPHABET, 2)
            key[a], key[b] = key[b], key[a]
            new_plaintext = _apply_key(ciphertext, key)
            new_score = bigram_log_probability(new_plaintext)

            # Exponential cooling calibrated for bigram range [-8.5, -4.0] (~4.5 units).
            # Linear schedule max(1.0, 10×...) was calibrated for the old -20 floor
            # (16-unit range) and runs as near-random-walk on the compressed range.
            temperature = max(0.1, 1.5 * math.exp(-3.0 * iteration / max_iterations))
            delta = new_score - current_score
            if delta > 0 or random.random() < math.exp(delta / temperature):
                current_score = new_score
                current_plaintext = new_plaintext
            else:
                key[a], key[b] = key[b], key[a]  # revert

        if current_score > best_overall_score:
            best_overall_score = current_score
            best_overall_plaintext = current_plaintext
            best_overall_key = dict(key)

    return best_overall_plaintext, best_overall_key, best_overall_score


class MonoalphabeticSolver(BaseSolver):
    name = "monoalphabetic"

    def __init__(self, max_iterations: int = 10000, restarts: int = 2):
        self.max_iterations = max_iterations
        self.restarts = restarts

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        plaintext, key, _ = solve_with_hill_climbing(
            ciphertext, self.max_iterations, self.restarts
        )
        sc = score_text(plaintext)
        confidence = ConfidenceLevel(classify_confidence(sc))

        # Format key as cipher→plain mapping for display
        key_display = {k: v for k, v in sorted(key.items())}
        return [
            CipherCandidate(
                cipher_type="monoalphabetic",
                plaintext=plaintext,
                key=key_display,
                confidence=confidence,
                language_score=sc,
                explanation=(
                    "Monoalphabetic substitution solved via simulated annealing "
                    f"({self.max_iterations} iterations × {self.restarts} restarts). "
                    "Key recovered using bigram frequency optimisation."
                ),
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        # Need enough text for meaningful frequency analysis
        return sum(1 for c in ciphertext if c.isalpha()) >= 20

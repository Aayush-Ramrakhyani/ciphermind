"""
/*
 * Index of Coincidence (IoC) utilities.
 * English plaintext: ~0.0665
 * Random / polyalphabetic: ~0.0385
 * Used for distinguishing monoalphabetic from polyalphabetic ciphers
 * and estimating Vigenère key length via the IoC-per-column method.
 */
"""

from __future__ import annotations

from collections import Counter
from typing import List


ENGLISH_IOC = 0.0665
RANDOM_IOC = 0.0385


def index_of_coincidence(text: str) -> float:
    """Compute IoC for all alphabetic characters in text."""
    letters = [c.lower() for c in text if c.isalpha()]
    n = len(letters)
    if n <= 1:
        return 0.0
    freq = Counter(letters)
    return sum(f * (f - 1) for f in freq.values()) / (n * (n - 1))


def average_ioc_for_key_length(text: str, key_length: int) -> float:
    """Average IoC across the key_length columns of text.

    If the correct key length is supplied the columns should each resemble
    monoalphabetically-shifted English (IoC ~ 0.065), confirming the guess.
    """
    letters = [c.lower() for c in text if c.isalpha()]
    if key_length <= 0 or len(letters) < key_length * 2:
        return 0.0
    columns = ["".join(letters[i::key_length]) for i in range(key_length)]
    iocs = [index_of_coincidence(col) for col in columns if col]
    return sum(iocs) / len(iocs) if iocs else 0.0


def best_key_lengths(text: str, max_length: int = 20) -> List[int]:
    """Return candidate key lengths sorted by how close their avg IoC is to English."""
    candidates = []
    for length in range(1, max_length + 1):
        avg_ioc = average_ioc_for_key_length(text, length)
        # higher avg IoC → more monoalphabetic per column → better candidate
        candidates.append((length, avg_ioc))
    # sort by distance from ENGLISH_IOC (ascending = closest first)
    candidates.sort(key=lambda x: abs(x[1] - ENGLISH_IOC))
    return [length for length, _ in candidates]


def classify_cipher_type(text: str) -> str:
    """Quick heuristic: monoalphabetic vs polyalphabetic vs random."""
    ioc = index_of_coincidence(text)
    if ioc >= 0.060:
        return "monoalphabetic"
    elif ioc >= 0.045:
        return "polyalphabetic"
    else:
        return "random_or_transposition"

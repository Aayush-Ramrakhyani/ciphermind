"""
/*
 * Columnar transposition cipher solver.
 * Tests column counts 2–10. For each column count, tries all permutations
 * of column order that are tractable (up to 7!) and scores each result.
 * For larger column counts uses a greedy frequency-based column ordering.
 */
"""

from __future__ import annotations

import itertools
import math
from typing import List

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text


def _columnar_decrypt(ciphertext: str, num_cols: int, col_order: List[int]) -> str:
    """Reconstruct plaintext given the column count and column reading order."""
    n = len(ciphertext)
    num_rows = math.ceil(n / num_cols)
    # Some columns may be shorter (incomplete last row)
    full_cols = n % num_cols  # number of shorter columns (0 means all full)
    col_lengths = []
    for c in range(num_cols):
        if full_cols == 0 or c < full_cols:
            col_lengths.append(num_rows)
        else:
            col_lengths.append(num_rows - 1)

    # Assign ciphertext to columns according to col_order
    cols = [""] * num_cols
    idx = 0
    for c in col_order:
        cols[c] = ciphertext[idx : idx + col_lengths[c]]
        idx += col_lengths[c]

    # Read row by row
    result = []
    for row in range(num_rows):
        for col in range(num_cols):
            if row < len(cols[col]):
                result.append(cols[col][row])
    return "".join(result)


def _greedy_column_order(ciphertext: str, num_cols: int) -> List[int]:
    """Order columns by their individual chi-squared score (heuristic)."""
    n = len(ciphertext)
    num_rows = math.ceil(n / num_cols)
    full_cols = n % num_cols

    col_scores = []
    start = 0
    for c in range(num_cols):
        length = num_rows if (full_cols == 0 or c < full_cols) else num_rows - 1
        col_text = ciphertext[start : start + length]
        # Score individually by bigram overlap within column
        from cryptanalysis.statistical.ngram import bigram_log_probability
        col_scores.append((c, bigram_log_probability(col_text)))
        start += length

    # Sort by descending score (best-looking columns first)
    col_scores.sort(key=lambda x: -x[1])
    return [c for c, _ in col_scores]


class ColumnarSolver(BaseSolver):
    name = "columnar"

    _BRUTE_FORCE_LIMIT = 7  # 7! = 5040, manageable

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        candidates = []
        for num_cols in range(2, min(11, len(ciphertext) + 1)):
            if num_cols <= self._BRUTE_FORCE_LIMIT:
                # Try every permutation
                for order in itertools.permutations(range(num_cols)):
                    plaintext = _columnar_decrypt(ciphertext, num_cols, list(order))
                    sc = score_text(plaintext)
                    confidence = ConfidenceLevel(classify_confidence(sc))
                    if confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.LIKELY):
                        candidates.append(
                            CipherCandidate(
                                cipher_type="columnar",
                                plaintext=plaintext,
                                key={"cols": num_cols, "order": list(order)},
                                confidence=confidence,
                                language_score=sc,
                                explanation=(
                                    f"Columnar transposition: {num_cols} columns, "
                                    f"reading order {list(order)}"
                                ),
                                metadata={"num_cols": num_cols, "order": list(order)},
                            )
                        )
            else:
                # Greedy heuristic for large column counts
                order = _greedy_column_order(ciphertext, num_cols)
                plaintext = _columnar_decrypt(ciphertext, num_cols, order)
                sc = score_text(plaintext)
                confidence = ConfidenceLevel(classify_confidence(sc))
                if confidence != ConfidenceLevel.NONE:
                    candidates.append(
                        CipherCandidate(
                            cipher_type="columnar",
                            plaintext=plaintext,
                            key={"cols": num_cols, "order": order},
                            confidence=confidence,
                            language_score=sc,
                            explanation=(
                                f"Columnar transposition: {num_cols} columns, "
                                f"greedy order {order}"
                            ),
                            metadata={"num_cols": num_cols, "order": order},
                        )
                    )

        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:5]

    def can_handle(self, ciphertext: str) -> bool:
        return len(ciphertext) >= 4

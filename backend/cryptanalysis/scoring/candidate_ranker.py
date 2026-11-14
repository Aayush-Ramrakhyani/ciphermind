"""
/*
 * Candidate ranker — merges, deduplicates, and ranks all CipherCandidates
 * produced by the various solvers into a final top-N list.
 *
 * Ranking priority:
 *   1. ConfidenceLevel (high > likely > possible > none)
 *   2. language_score (descending)
 *   3. Simplicity of cipher type (simpler ciphers ranked above complex ones
 *      when scores are equal, following Occam's razor)
 */
"""

from __future__ import annotations

from typing import List

from cryptanalysis.base import CipherCandidate, ConfidenceLevel

_CONFIDENCE_ORDER = {
    ConfidenceLevel.HIGH: 3,
    ConfidenceLevel.LIKELY: 2,
    ConfidenceLevel.POSSIBLE: 1,
    ConfidenceLevel.NONE: 0,
}

# Lower = simpler (ranked higher when scores are tied)
_CIPHER_COMPLEXITY = {
    "rot13": 0, "rot5": 0, "rot18": 0, "rot47": 0,
    "atbash": 1, "caesar": 2,
    "hex": 3, "base64": 3, "binary": 3, "morse": 3, "url_encoding": 3,
    "affine": 4, "rail_fence": 5, "columnar": 6,
    "vigenere": 7, "monoalphabetic": 8, "playfair": 9,
}


def _rank_key(candidate: CipherCandidate) -> tuple:
    return (
        -_CONFIDENCE_ORDER.get(candidate.confidence, 0),
        -candidate.language_score,
        _CIPHER_COMPLEXITY.get(candidate.cipher_type, 10),
    )


def rank_candidates(all_candidates: List[CipherCandidate], top_n: int = 5) -> List[CipherCandidate]:
    """Return the top_n best candidates after deduplication and ranking."""
    if not all_candidates:
        return []

    # Deduplicate: keep only the best-scoring candidate per (cipher_type, plaintext[:50])
    seen: dict = {}
    for c in all_candidates:
        key = (c.cipher_type, c.plaintext[:50].lower().strip())
        if key not in seen or c.language_score > seen[key].language_score:
            seen[key] = c

    deduped = list(seen.values())
    deduped.sort(key=_rank_key)
    return deduped[:top_n]

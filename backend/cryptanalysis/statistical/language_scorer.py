"""
/*
 * Language scorer -- unified scoring surface used by all cipher solvers.
 * Combines chi-squared, bigram log-probability, and word-frequency signals
 * into a single normalised score [0.0, 1.0] where 1.0 = perfect English.
 */
"""

from __future__ import annotations

from cryptanalysis.statistical.frequency import chi_squared, word_frequency_score
from cryptanalysis.statistical.ngram import bigram_log_probability, trigram_log_probability

_CHI2_BAD   = 2.0   # chi-squared above this = not English (for 50+ alpha chars)
_BIGRAM_BAD  = -7.5; _BIGRAM_GOOD  = -2.5
_TRIGRAM_BAD = -8.0; _TRIGRAM_GOOD = -5.0
_MIN_ALPHA_RATIO = 0.30


def score_text(text: str) -> float:
    """Return a composite English-language score [0.0, 1.0]."""
    alpha_chars = sum(1 for c in text if c.isalpha())
    if alpha_chars == 0:
        return 0.0
    alpha_ratio = alpha_chars / max(len(text), 1)
    if alpha_ratio < _MIN_ALPHA_RATIO:
        return 0.0
    alpha_weight = min(1.0, alpha_ratio / 0.60)

    # 1. Chi-squared — scale tolerance up for short texts (chi2 is noisy below 50 chars)
    chi2 = chi_squared(text)
    chi2_bad = _CHI2_BAD * max(1.0, 50.0 / alpha_chars)
    chi_score = max(0.0, 1.0 - chi2 / chi2_bad)

    # 2. Bigram log-probability
    blp = bigram_log_probability(text)
    bigram_score = max(0.0, min((blp - _BIGRAM_BAD) / (_BIGRAM_GOOD - _BIGRAM_BAD), 1.0))

    # 3. Trigram log-probability (more discriminative than bigrams)
    tlp = trigram_log_probability(text)
    trigram_score = max(0.0, min((tlp - _TRIGRAM_BAD) / (_TRIGRAM_GOOD - _TRIGRAM_BAD), 1.0))

    # 4. Word frequency — most reliable signal, especially for short texts
    word_score = word_frequency_score(text)

    # Short texts: lean heavily on word_score; long texts: all signals contribute
    t = min(1.0, alpha_chars / 80.0)
    combined = (
        0.10 * t         * chi_score    +
        0.20             * bigram_score +
        0.25             * trigram_score +
        (0.45 + 0.10 * (1 - t)) * word_score
    )
    return round(combined * alpha_weight, 4)


def classify_confidence(score: float) -> str:
    """Map a composite score to a confidence label."""
    if score >= 0.70:
        return "high"
    elif score >= 0.45:
        return "likely"
    elif score >= 0.20:
        return "possible"
    else:
        return "none"

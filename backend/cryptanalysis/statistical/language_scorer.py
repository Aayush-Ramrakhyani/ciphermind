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


# Chi-squared reference range: typical English prose ~0.03-0.10; gibberish > 1.0
_CHI2_BAD = 2.0
_CHI2_GOOD = 0.03

# Bigram log-prob reference range (normalised per bigram, floor now -8.5)
_BIGRAM_BAD = -7.5   # near-uniform / random text
_BIGRAM_GOOD = -2.5  # clean English prose

# Minimum alpha-to-total ratio -- cipher outputs that are mostly non-alpha
# (e.g. affine-decoding a hex string gives mostly digits) are penalised to 0
_MIN_ALPHA_RATIO = 0.30


def score_text(text: str) -> float:
    """Return a composite English-language score [0.0, 1.0]."""
    alpha_chars = sum(1 for c in text if c.isalpha())
    if alpha_chars == 0:
        return 0.0

    # Penalise text with very few alpha chars vs total (non-decoded outputs)
    total_chars = len(text)
    alpha_ratio = alpha_chars / max(total_chars, 1)
    if alpha_ratio < _MIN_ALPHA_RATIO:
        return 0.0
    # Smooth ramp: full weight at >=60% alpha
    alpha_weight = min(1.0, alpha_ratio / 0.60)

    # 1. Chi-squared contribution (lower chi2 = more English-like)
    chi2 = chi_squared(text)
    chi_score = 1.0 - min(chi2 / _CHI2_BAD, 1.0)
    chi_score = max(chi_score - (_CHI2_GOOD / _CHI2_BAD), 0.0)

    # 2. Bigram log-probability contribution
    blp = bigram_log_probability(text)
    bigram_score = (blp - _BIGRAM_BAD) / (_BIGRAM_GOOD - _BIGRAM_BAD)
    bigram_score = max(0.0, min(bigram_score, 1.0))

    # 3. Word frequency contribution (strong signal for decoded English)
    word_score = word_frequency_score(text)

    # Weighted combination -- increased word_score weight for short-text robustness
    combined = 0.30 * chi_score + 0.40 * bigram_score + 0.30 * word_score
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

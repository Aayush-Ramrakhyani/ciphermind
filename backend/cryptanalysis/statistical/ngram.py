"""
/*
 * N-gram frequency analysis.
 * Provides log-probability scoring using embedded English bigram/trigram tables.
 * Log-probability scoring is robust against text length variation.
 */
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Dict

# Top English bigram frequencies (normalised to probabilities)
# Source: Practical Cryptography / Peter Norvig's data
ENGLISH_BIGRAMS: Dict[str, float] = {
    "th": 0.0271, "he": 0.0233, "in": 0.0203, "er": 0.0178, "an": 0.0161,
    "re": 0.0141, "on": 0.0132, "at": 0.0120, "en": 0.0113, "nd": 0.0107,
    "ti": 0.0105, "es": 0.0100, "or": 0.0100, "te": 0.0094, "of": 0.0094,
    "ed": 0.0093, "is": 0.0092, "it": 0.0088, "al": 0.0087, "ar": 0.0084,
    "st": 0.0082, "to": 0.0079, "nt": 0.0079, "ng": 0.0074, "se": 0.0074,
    "ha": 0.0073, "as": 0.0073, "ou": 0.0072, "io": 0.0071, "le": 0.0069,
    "ve": 0.0069, "co": 0.0063, "me": 0.0062, "de": 0.0062, "hi": 0.0060,
    "ri": 0.0059, "ro": 0.0057, "ic": 0.0055, "ne": 0.0054, "ea": 0.0053,
    "ra": 0.0053, "ce": 0.0052, "li": 0.0052, "ch": 0.0051, "ll": 0.0050,
    "be": 0.0049, "ma": 0.0049, "si": 0.0049, "om": 0.0048, "ur": 0.0048,
    "ca": 0.0047, "el": 0.0045, "ta": 0.0044, "la": 0.0044, "ns": 0.0044,
    "di": 0.0044, "fo": 0.0043, "ho": 0.0043, "pe": 0.0043, "ss": 0.0042,
    "ut": 0.0042, "we": 0.0042, "no": 0.0041, "ot": 0.0041, "un": 0.0041,
    "if": 0.0040, "wi": 0.0040, "wh": 0.0040, "ge": 0.0039, "ee": 0.0039,
    "ly": 0.0039, "eb": 0.0001, "tt": 0.0032, "so": 0.0036, "fi": 0.0035,
    "us": 0.0033, "wa": 0.0033, "pl": 0.0032, "pr": 0.0032, "pa": 0.0031,
    "wo": 0.0030, "na": 0.0030, "po": 0.0030, "il": 0.0029, "am": 0.0028,
    "lo": 0.0028, "ni": 0.0028, "ts": 0.0027, "ad": 0.0027, "ew": 0.0027,
    "ye": 0.0001, "id": 0.0027, "sp": 0.0026, "mi": 0.0026, "tr": 0.0026,
    "ly": 0.0025, "mo": 0.0025, "ow": 0.0025, "ab": 0.0024, "rs": 0.0024,
    "do": 0.0023, "ag": 0.0023, "ai": 0.0022, "em": 0.0022, "oo": 0.0022,
    "im": 0.0021, "ac": 0.0021, "bu": 0.0021, "ci": 0.0021, "ds": 0.0021,
    "fr": 0.0021, "go": 0.0021, "ie": 0.0020, "iv": 0.0020, "ly": 0.0020,
    "op": 0.0019, "qu": 0.0019, "rt": 0.0019, "sh": 0.0019, "su": 0.0019,
    "ad": 0.0018, "af": 0.0018, "ap": 0.0018, "av": 0.0018, "ba": 0.0018,
    "bl": 0.0018, "bo": 0.0018, "br": 0.0018, "cl": 0.0018, "cr": 0.0018,
    "cu": 0.0018, "da": 0.0018, "dr": 0.0018, "du": 0.0018, "ec": 0.0018,
    "ef": 0.0017, "eg": 0.0017, "ei": 0.0017, "ek": 0.0001, "ep": 0.0017,
    "eq": 0.0001, "et": 0.0017, "eu": 0.0005, "ev": 0.0017, "ew": 0.0017,
    "ex": 0.0017, "ey": 0.0017, "ez": 0.0001, "fa": 0.0017, "fe": 0.0017,
    "ff": 0.0005, "fl": 0.0017, "fu": 0.0017, "fy": 0.0001, "ga": 0.0017,
    "gh": 0.0017, "gi": 0.0017, "gl": 0.0001, "gn": 0.0001, "gr": 0.0017,
    "gu": 0.0001, "gy": 0.0001, "ha": 0.0073, "hd": 0.0001, "hm": 0.0001,
    "hr": 0.0001, "hs": 0.0001, "ht": 0.0005, "hu": 0.0005, "hy": 0.0005,
}

# Top English trigrams
ENGLISH_TRIGRAMS: Dict[str, float] = {
    "the": 0.0181, "and": 0.0073, "ing": 0.0072, "ion": 0.0042, "ent": 0.0042,
    "ati": 0.0040, "for": 0.0038, "her": 0.0036, "ter": 0.0035, "hat": 0.0034,
    "tha": 0.0033, "ere": 0.0031, "ate": 0.0031, "his": 0.0030, "con": 0.0030,
    "res": 0.0029, "ver": 0.0028, "all": 0.0028, "ons": 0.0027, "nce": 0.0027,
    "men": 0.0026, "ith": 0.0026, "ted": 0.0026, "ers": 0.0026, "pro": 0.0025,
    "thi": 0.0025, "wit": 0.0025, "are": 0.0024, "ess": 0.0024, "not": 0.0024,
    "ive": 0.0024, "was": 0.0024, "ect": 0.0023, "rea": 0.0023, "com": 0.0023,
    "eve": 0.0023, "per": 0.0023, "int": 0.0022, "est": 0.0022, "sta": 0.0022,
    "cti": 0.0022, "ica": 0.0021, "ist": 0.0021, "ear": 0.0021, "ain": 0.0021,
    "one": 0.0021, "our": 0.0021, "iti": 0.0020, "rat": 0.0020, "nte": 0.0020,
    "can": 0.0020, "str": 0.0020, "hin": 0.0019, "you": 0.0019, "ure": 0.0019,
    "ous": 0.0019, "tio": 0.0019, "has": 0.0019, "had": 0.0018, "uld": 0.0018,
    "ort": 0.0018, "ally": 0.0005, "oth": 0.0017, "out": 0.0017, "nal": 0.0017,
    "les": 0.0017, "sin": 0.0017, "ome": 0.0017, "ven": 0.0017, "she": 0.0016,
    "nde": 0.0016, "ind": 0.0016, "tor": 0.0016, "tal": 0.0016, "ert": 0.0016,
    "ren": 0.0016, "tan": 0.0016, "dis": 0.0016, "ary": 0.0015, "nit": 0.0015,
    "pre": 0.0015, "nto": 0.0015, "and": 0.0073, "ati": 0.0040, "sed": 0.0014,
    "enc": 0.0014, "ble": 0.0014, "iti": 0.0014, "hat": 0.0034, "cal": 0.0013,
    "ome": 0.0017, "unt": 0.0013, "get": 0.0013, "nal": 0.0017, "lay": 0.0013,
    "ple": 0.0013, "mor": 0.0013, "ref": 0.0013, "set": 0.0013, "ugh": 0.0013,
}

_LOG_MIN = -8.5  # floor log-probability for unseen/rare n-grams (not -20 which is too extreme)


def _log_prob(freq: float) -> float:
    return math.log(freq) if freq > 0 else _LOG_MIN


# Precompute log tables
_BIGRAM_LOG: Dict[str, float] = {bg: _log_prob(p) for bg, p in ENGLISH_BIGRAMS.items()}
_TRIGRAM_LOG: Dict[str, float] = {tg: _log_prob(p) for tg, p in ENGLISH_TRIGRAMS.items()}


def bigram_log_probability(text: str) -> float:
    """Sum of log-probabilities for all bigrams in text (normalised by count)."""
    text = "".join(c.lower() for c in text if c.isalpha())
    if len(text) < 2:
        return _LOG_MIN
    total = 0.0
    for i in range(len(text) - 1):
        bg = text[i : i + 2]
        total += _BIGRAM_LOG.get(bg, _LOG_MIN)
    return total / (len(text) - 1)


def trigram_log_probability(text: str) -> float:
    """Sum of log-probabilities for all trigrams in text (normalised by count)."""
    text = "".join(c.lower() for c in text if c.isalpha())
    if len(text) < 3:
        return _LOG_MIN
    total = 0.0
    for i in range(len(text) - 2):
        tg = text[i : i + 3]
        total += _TRIGRAM_LOG.get(tg, _LOG_MIN)
    return total / (len(text) - 2)


def repeated_sequence_analysis(text: str, min_len: int = 3) -> Dict[str, int]:
    """Find repeated sequences of length >= min_len in text (Kasiski preprocessing)."""
    text_clean = "".join(c.lower() for c in text if c.isalpha())
    seen: Dict[str, int] = {}
    for i in range(len(text_clean) - min_len + 1):
        for length in range(min_len, min(20, len(text_clean) - i + 1)):
            seq = text_clean[i : i + length]
            if seq in seen:
                seen[seq] += 1
            else:
                seen[seq] = 1
    return {k: v for k, v in seen.items() if v > 1}

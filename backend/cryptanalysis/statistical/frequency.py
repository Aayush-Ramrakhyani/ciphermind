"""
/*
 * Letter frequency analysis utilities.
 * Reference English frequencies from Lewand (2000) / Wikipedia.
 */
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple


ENGLISH_UNIGRAM_FREQ: Dict[str, float] = {
    "a": 0.08167, "b": 0.01492, "c": 0.02782, "d": 0.04253,
    "e": 0.12702, "f": 0.02228, "g": 0.02015, "h": 0.06094,
    "i": 0.06966, "j": 0.00153, "k": 0.00772, "l": 0.04025,
    "m": 0.02406, "n": 0.06749, "o": 0.07507, "p": 0.01929,
    "q": 0.00095, "r": 0.05987, "s": 0.06327, "t": 0.09056,
    "u": 0.02758, "v": 0.00978, "w": 0.02360, "x": 0.00150,
    "y": 0.01974, "z": 0.00074,
}

# Most common English words (top-200 by frequency)
COMMON_ENGLISH_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "great", "between", "need",
    "large", "often", "hand", "high", "place", "hold", "world", "where",
    "help", "through", "much", "before", "line", "right", "too", "mean",
    "old", "any", "same", "tell", "boy", "follow", "came", "want", "show",
    "also", "around", "farm", "three", "small", "set", "put", "end", "does",
    "another", "well", "large", "must", "big", "even", "such", "because",
    "turn", "here", "why", "ask", "went", "men", "read", "need", "land",
    "different", "home", "us", "move", "try", "kind", "hand", "picture",
    "again", "change", "off", "play", "spell", "air", "away", "animal",
    "house", "point", "page", "letter", "mother", "answer", "found",
    "study", "still", "learn", "plant", "cover", "food", "sun", "four",
    "between", "state", "keep", "eye", "never", "last", "let", "thought",
    "city", "tree", "cross", "farm", "hard", "start", "might", "story",
    "saw", "far", "sea", "draw", "left", "late", "run", "while", "press",
    "close", "night", "real", "life", "few", "north", "open", "seem",
    "together", "next", "white", "children", "begin", "got", "walk", "example",
    "ease", "paper", "group", "always", "music", "those", "both", "mark",
    "book", "carry", "took", "science", "eat", "room", "friend", "began",
    "idea", "fish", "mountain", "stop", "once", "base", "hear", "horse",
    "cut", "sure", "watch", "color", "face", "wood", "main", "enough",
    "plain", "girl", "usual", "young", "ready", "above", "ever", "red",
    "list", "though", "feel", "talk", "bird", "soon", "body", "dog", "family",
    "direct", "pose", "leave", "song", "measure", "door", "product", "black",
    "short", "numeral", "class", "wind", "question", "happen", "complete",
    "ship", "area", "half", "rock", "order", "fire", "south", "problem",
    "piece", "told", "knew", "pass", "since", "top", "whole", "king", "space",
    "heard", "best", "hour", "better", "true", "during", "hundred", "five",
    "remember", "step", "early", "hold", "west", "ground", "interest", "reach",
    "fast", "verb", "sing", "listen", "six", "table", "travel", "less",
    "morning", "ten", "simple", "several", "vowel", "toward", "war", "lay",
    "against", "pattern", "slow", "center", "love", "person", "money",
    "serve", "appear", "road", "map", "rain", "rule", "govern", "pull",
    "cold", "notice", "voice", "unit", "power", "town", "fine", "drive",
    "been", "front", "teach", "week", "final", "gave", "green", "oh",
    "quick", "develop", "ocean", "warm", "free", "minute", "strong", "special",
    "behind", "clear", "tail", "produce", "fact", "street", "inch", "multiply",
    "nothing", "course", "stay", "wheel", "full", "force", "blue", "object",
    "decide", "surface", "deep", "moon", "island", "foot", "system", "busy",
    "test", "record", "boat", "common", "gold", "possible", "plane", "age",
    "dry", "wonder", "laugh", "thousand", "ago", "ran", "check", "game",
    "shape", "equate", "hot", "miss", "brought", "heat", "snow", "tire",
    "bring", "yes", "distant", "fill", "east", "paint", "language", "among",
}


def letter_frequencies(text: str) -> Dict[str, float]:
    """Return normalised letter frequency map for the given text."""
    letters = [c.lower() for c in text if c.isalpha()]
    if not letters:
        return {}
    total = len(letters)
    counts = Counter(letters)
    return {ch: counts.get(ch, 0) / total for ch in "abcdefghijklmnopqrstuvwxyz"}


def chi_squared(text: str, expected: Dict[str, float] = None) -> float:
    """Chi-squared statistic comparing text letter distribution to English.

    Lower value = closer to expected English distribution.
    """
    if expected is None:
        expected = ENGLISH_UNIGRAM_FREQ
    obs = letter_frequencies(text)
    total = sum(1 for c in text if c.isalpha())
    if total == 0:
        return float("inf")
    chi2 = 0.0
    for letter in "abcdefghijklmnopqrstuvwxyz":
        o = obs.get(letter, 0.0)
        e = expected.get(letter, 1e-9)
        chi2 += ((o - e) ** 2) / e
    return chi2


def word_frequency_score(text: str) -> float:
    """Fraction of tokens in text that are common English words [0.0, 1.0]."""
    words = [w.strip(".,!?;:\"'()[]{}").lower() for w in text.split()]
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
    return hits / len(words)


def sorted_frequency_string(text: str) -> str:
    """Return letters sorted by descending frequency in text."""
    freqs = letter_frequencies(text)
    return "".join(sorted(freqs, key=lambda c: -freqs[c]))

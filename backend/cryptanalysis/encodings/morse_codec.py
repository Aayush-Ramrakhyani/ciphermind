"""
/*
 * Morse code decoder.
 * Accepts dots/dashes separated by spaces for letters and / or | for words.
 */
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

_MORSE_TABLE: Dict[str, str] = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z", "-----": "0", ".----": "1", "..---": "2", "...--": "3",
    "....-": "4", ".....": "5", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9", ".-.-.-": ".", "--..--": ",", "..--..": "?",
    ".----.": "'", "-.-.--": "!", "-..-.": "/", "-.--.": "(",
    "-.--.-": ")", ".-...": "&", "---...": ":", "-.-.-.": ";",
    "-...-": "=", ".-.-.": "+", "-....-": "-", "..--.-": "_",
    ".-..-.": '"', "...-..-": "$", ".--.-.": "@",
}

_MORSE_PATTERN = re.compile(r"^[.\- /|]+$")


def _try_decode(text: str) -> Optional[str]:
    text = text.strip()
    # Normalise word separators
    text = re.sub(r"\s*[/|]\s*", " / ", text)
    words_raw = text.split(" / ")
    decoded_words = []
    for word_str in words_raw:
        letter_codes = word_str.split()
        decoded_letters = []
        for code in letter_codes:
            ch = _MORSE_TABLE.get(code)
            if ch is None:
                return None  # unrecognised symbol → not Morse
            decoded_letters.append(ch)
        decoded_words.append("".join(decoded_letters))
    return " ".join(decoded_words)


class MorseSolver(BaseSolver):
    name = "morse"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        decoded = _try_decode(ciphertext)
        if decoded is None:
            return []
        sc = score_text(decoded)
        content_confidence = ConfidenceLevel(classify_confidence(sc))
        if content_confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.HIGH
        elif sc > 0.05:
            confidence = ConfidenceLevel.LIKELY
        else:
            confidence = content_confidence
        return [
            CipherCandidate(
                cipher_type="morse",
                plaintext=decoded,
                key="morse",
                confidence=confidence,
                language_score=sc,
                explanation="Decoded from Morse code (dots and dashes) — structural detection confirmed",
            )
        ]

    def can_handle(self, ciphertext: str) -> bool:
        return bool(_MORSE_PATTERN.match(ciphertext.strip())) and len(ciphertext.strip()) >= 1

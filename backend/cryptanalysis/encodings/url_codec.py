"""
/*
 * URL and Unicode escape encoding detector and decoder.
 * Handles: percent-encoded URLs, Unicode escapes (\\uXXXX), HTML entities.
 */
"""

from __future__ import annotations

import html
import re
from urllib.parse import unquote, unquote_plus

from typing import List, Optional

from cryptanalysis.base import BaseSolver, CipherCandidate, ConfidenceLevel
from cryptanalysis.statistical.language_scorer import classify_confidence, score_text

_URL_PATTERN = re.compile(r"%[0-9A-Fa-f]{2}")
_UNICODE_PATTERN = re.compile(r"\\u[0-9A-Fa-f]{4}")
_HTML_ENTITY_PATTERN = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|[a-zA-Z]+);")


def _try_url_decode(text: str) -> Optional[str]:
    if not _URL_PATTERN.search(text):
        return None
    try:
        decoded = unquote(text)
        return decoded if decoded != text else None
    except Exception:
        return None


def _try_unicode_decode(text: str) -> Optional[str]:
    if not _UNICODE_PATTERN.search(text):
        return None
    try:
        decoded = text.encode("utf-8").decode("unicode_escape")
        return decoded
    except Exception:
        return None


def _try_html_decode(text: str) -> Optional[str]:
    if not _HTML_ENTITY_PATTERN.search(text):
        return None
    decoded = html.unescape(text)
    return decoded if decoded != text else None


class UrlSolver(BaseSolver):
    name = "url_encoding"

    def solve(self, ciphertext: str) -> List[CipherCandidate]:
        candidates = []
        for decoder_name, decoder_fn in [
            ("URL percent-encoding", _try_url_decode),
            ("Unicode escape (\\uXXXX)", _try_unicode_decode),
            ("HTML entities", _try_html_decode),
        ]:
            decoded = decoder_fn(ciphertext)
            if decoded is None:
                continue
            sc = score_text(decoded)
            confidence = ConfidenceLevel(classify_confidence(sc))
            boosted = ConfidenceLevel.HIGH if confidence == ConfidenceLevel.HIGH else ConfidenceLevel.LIKELY
            candidates.append(
                CipherCandidate(
                    cipher_type="url_encoding",
                    plaintext=decoded,
                    key=decoder_name,
                    confidence=boosted,
                    language_score=sc,
                    explanation=f"Decoded from {decoder_name} — structural detection confirmed",
                )
            )
        candidates.sort(key=lambda c: -c.language_score)
        return candidates[:2]

    def can_handle(self, ciphertext: str) -> bool:
        return bool(
            _URL_PATTERN.search(ciphertext)
            or _UNICODE_PATTERN.search(ciphertext)
            or _HTML_ENTITY_PATTERN.search(ciphertext)
        )

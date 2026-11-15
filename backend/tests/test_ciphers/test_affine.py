"""
/*
 * Unit tests for the Affine cipher solver.
 * Tests: decryption correctness for all valid (a, b) pairs, solver ranking.
 */
"""

import pytest

from cryptanalysis.ciphers.affine import AffineSolver, affine_decrypt, _VALID_A
from cryptanalysis.base import ConfidenceLevel


def _affine_encrypt(text: str, a: int, b: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            x = ord(ch.lower()) - ord("a")
            enc = (a * x + b) % 26
            letter = chr(enc + ord("a"))
            result.append(letter.upper() if ch.isupper() else letter)
        else:
            result.append(ch)
    return "".join(result)


class TestAffineDecrypt:
    def test_known_key(self):
        pt = "HELLOWORLD"
        ct = _affine_encrypt(pt, 7, 3)
        decrypted = affine_decrypt(ct, 7, 3)
        assert decrypted.upper() == pt

    def test_all_valid_a_values(self):
        for a in _VALID_A:
            for b in [0, 5, 13, 25]:
                ct = _affine_encrypt("THEQUICKBROWNFOX", a, b)
                decrypted = affine_decrypt(ct, a, b)
                assert decrypted.upper() == "THEQUICKBROWNFOX"

    def test_invalid_a_returns_none(self):
        assert affine_decrypt("HELLO", 2, 3) is None  # 2 not coprime to 26

    def test_preserves_spaces_and_punctuation(self):
        ct = _affine_encrypt("Hello, World!", 5, 8)
        pt = affine_decrypt(ct, 5, 8)
        assert pt and ", " in pt and "!" in pt


class TestAffineSolver:
    def test_recovers_key_a7_b3(self):
        plaintext = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
        ct = _affine_encrypt(plaintext, 7, 3)
        solver = AffineSolver()
        candidates = solver.solve(ct)
        assert any(
            c.key == {"a": 7, "b": 3} for c in candidates
        ), f"Key (7,3) not in candidates: {[c.key for c in candidates]}"

    def test_top_candidate_has_acceptable_confidence(self):
        plaintext = "CRYPTOGRAPHY IS THE SCIENCE OF SECRET WRITING"
        ct = _affine_encrypt(plaintext, 11, 7)
        solver = AffineSolver()
        candidates = solver.solve(ct)
        assert candidates
        assert candidates[0].confidence != ConfidenceLevel.NONE

    def test_can_handle(self):
        solver = AffineSolver()
        assert solver.can_handle("ABCDEF") is True
        assert solver.can_handle("AB") is False

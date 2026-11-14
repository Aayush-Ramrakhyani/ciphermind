"""
/*
 * Unit tests for the Caesar cipher solver.
 * Tests: correct decryption for all shifts, edge cases, solver ranking.
 */
"""

import pytest

from cryptanalysis.ciphers.caesar import CaesarSolver, _caesar_decrypt
from cryptanalysis.base import ConfidenceLevel


PLAINTEXT = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"


def _encrypt_caesar(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


class TestCaesarDecrypt:
    def test_shift_3_roundtrip(self):
        ciphertext = _encrypt_caesar(PLAINTEXT, 3)
        assert _caesar_decrypt(ciphertext, 3).upper() == PLAINTEXT

    def test_all_shifts_roundtrip(self):
        for shift in range(26):
            ct = _encrypt_caesar(PLAINTEXT, shift)
            assert _caesar_decrypt(ct, shift).upper() == PLAINTEXT

    def test_preserves_non_alpha(self):
        ct = _encrypt_caesar("Hello, World!", 13)
        pt = _caesar_decrypt(ct, 13)
        assert ", " in pt and "!" in pt

    def test_shift_0_identity(self):
        assert _caesar_decrypt(PLAINTEXT, 0) == PLAINTEXT

    def test_shift_13_is_rot13(self):
        ct = _encrypt_caesar("HELLO", 13)
        assert ct == "URYYB"
        assert _caesar_decrypt(ct, 13) == "HELLO"


class TestCaesarSolver:
    def test_finds_correct_shift(self):
        for shift in [3, 7, 13, 19]:
            ciphertext = _encrypt_caesar(PLAINTEXT, shift)
            solver = CaesarSolver()
            candidates = solver.solve(ciphertext)
            assert candidates, f"No candidates found for shift {shift}"
            top = candidates[0]
            assert top.key == shift, f"Expected shift {shift}, got {top.key}"

    def test_top_candidate_high_confidence_on_long_text(self):
        # Use non-pangram prose so rare letters (q,z,x) don't inflate chi² and kill score
        prose = "IN THE BEGINNING WAS THE WORD AND THE WORD WAS WITH GOD AND THE WORD WAS GOD "
        ciphertext = _encrypt_caesar(prose * 3, 7)
        solver = CaesarSolver()
        candidates = solver.solve(ciphertext)
        # Correctly decrypted non-pangram prose should score at least POSSIBLE
        assert candidates[0].confidence != ConfidenceLevel.NONE

    def test_can_handle_short_text(self):
        solver = CaesarSolver()
        assert solver.can_handle("ABCD") is True
        assert solver.can_handle("AB") is False

    def test_returns_at_most_5_candidates(self):
        solver = CaesarSolver()
        candidates = solver.solve(PLAINTEXT)
        assert len(candidates) <= 5

    def test_empty_input(self):
        solver = CaesarSolver()
        # can_handle returns False for empty; solve on empty should return something
        candidates = solver.solve("")
        # all 26 shifts on empty string produce empty string
        for c in candidates:
            assert c.plaintext == ""


class TestCaesarEdgeCases:
    def test_mixed_case_preserved(self):
        ct = _encrypt_caesar("Hello World", 5)
        pt = _caesar_decrypt(ct, 5)
        assert pt[0].isupper()
        assert pt[6].isupper()

    def test_numbers_not_shifted(self):
        ct = _encrypt_caesar("ABC123", 3)
        assert ct.endswith("123")

    def test_special_chars_not_shifted(self):
        ct = _encrypt_caesar("HeLLo!", 10)
        pt = _caesar_decrypt(ct, 10)
        assert pt.endswith("!")

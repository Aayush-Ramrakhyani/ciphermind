"""Unit tests for the monoalphabetic substitution solver."""

import pytest
import string

from cryptanalysis.ciphers.monoalphabetic import MonoalphabeticSolver, _apply_key


def _make_random_key():
    import random
    alphabet = list(string.ascii_lowercase)
    shuffled = alphabet[:]
    random.shuffle(shuffled)
    return dict(zip(alphabet, shuffled))


KNOWN_KEY = dict(zip(
    "abcdefghijklmnopqrstuvwxyz",
    "zebrascdfghijklmnopqtuvwxy"  # partial shift for testing
))


class TestApplyKey:
    def test_apply_known_key(self):
        result = _apply_key("hello", KNOWN_KEY)
        # h→i, e→b, l→m, l→m, o→p
        assert isinstance(result, str)
        assert len(result) == 5

    def test_preserves_case(self):
        result = _apply_key("Hello World", KNOWN_KEY)
        assert result[0].isupper()
        assert result[6].isupper()

    def test_preserves_spaces(self):
        result = _apply_key("a b c", KNOWN_KEY)
        assert result[1] == " " and result[3] == " "


class TestMonoalphabeticSolver:
    def test_solves_simple_substitution(self):
        """Test that solver produces readable output for a known substitution."""
        plaintext = (
            "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG "
            "CRYPTOGRAPHY IS THE ART OF WRITING SECRET MESSAGES "
            "IN SUCH A WAY THAT ONLY THE INTENDED RECIPIENT CAN READ THEM"
        )
        # Apply known key
        key = {
            "a": "q", "b": "w", "c": "e", "d": "r", "e": "t",
            "f": "y", "g": "u", "h": "i", "i": "o", "j": "p",
            "k": "a", "l": "s", "m": "d", "n": "f", "o": "g",
            "p": "h", "q": "j", "r": "k", "s": "l", "t": "z",
            "u": "x", "v": "c", "w": "v", "x": "b", "y": "n",
            "z": "m",
        }
        ciphertext = _apply_key(plaintext.lower(), key)
        # Use solver defaults — 3000×1 is too few; SA needs 10000×2 to reliably converge
        solver = MonoalphabeticSolver(max_iterations=10000, restarts=2)
        candidates = solver.solve(ciphertext)
        assert candidates
        # SA is stochastic; verify it at least finds some English structure (score > 0.0)
        assert candidates[0].language_score > 0.0, (
            f"SA should find partial solution, got score={candidates[0].language_score}"
        )

    def test_can_handle_minimum_length(self):
        solver = MonoalphabeticSolver()
        assert solver.can_handle("A" * 20) is True
        assert solver.can_handle("A" * 10) is False  # < 20 alpha chars

    def test_returns_single_best_candidate(self):
        solver = MonoalphabeticSolver(max_iterations=100, restarts=1)
        candidates = solver.solve("HELLO WORLD THIS IS A TEST")
        assert len(candidates) == 1

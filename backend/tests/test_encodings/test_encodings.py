"""
/*
 * Unit tests for all encoding solvers.
 * Tests: Base64, Hex, Binary, Morse, URL/Unicode encoding detection and decoding.
 */
"""

import base64
import pytest

from cryptanalysis.encodings.base64_codec import Base64Solver
from cryptanalysis.encodings.hex_codec import HexSolver
from cryptanalysis.encodings.binary_codec import BinarySolver
from cryptanalysis.encodings.morse_codec import MorseSolver
from cryptanalysis.encodings.url_codec import UrlSolver


class TestBase64Solver:
    def test_decodes_standard_base64(self):
        plaintext = "Hello, World!"
        encoded = base64.b64encode(plaintext.encode()).decode()
        solver = Base64Solver()
        candidates = solver.solve(encoded)
        assert candidates
        assert candidates[0].plaintext == plaintext

    def test_decodes_url_safe_base64(self):
        plaintext = "Hello World"
        encoded = base64.urlsafe_b64encode(plaintext.encode()).decode()
        solver = Base64Solver()
        candidates = solver.solve(encoded)
        assert candidates
        assert "Hello" in candidates[0].plaintext

    def test_decodes_without_padding(self):
        encoded = base64.b64encode(b"test").decode().rstrip("=")
        solver = Base64Solver()
        candidates = solver.solve(encoded)
        assert candidates

    def test_invalid_base64_returns_empty(self):
        solver = Base64Solver()
        candidates = solver.solve("not!valid@base64#")
        assert candidates == []

    def test_can_handle_valid(self):
        solver = Base64Solver()
        assert solver.can_handle("SGVsbG8=") is True
        assert solver.can_handle("not base 64!!!") is False


class TestHexSolver:
    def test_decodes_lowercase_hex(self):
        encoded = "48656c6c6f"
        solver = HexSolver()
        candidates = solver.solve(encoded)
        assert candidates
        assert candidates[0].plaintext == "Hello"

    def test_decodes_uppercase_hex(self):
        solver = HexSolver()
        candidates = solver.solve("48656C6C6F")
        assert candidates
        assert candidates[0].plaintext == "Hello"

    def test_decodes_0x_prefixed(self):
        solver = HexSolver()
        candidates = solver.solve("0x48656c6c6f")
        assert candidates

    def test_odd_length_returns_empty(self):
        solver = HexSolver()
        assert solver.can_handle("abc") is False

    def test_invalid_hex_returns_empty(self):
        solver = HexSolver()
        candidates = solver.solve("GGGG")
        assert candidates == []


class TestBinarySolver:
    def test_decodes_spaced_binary(self):
        # "Hi" in binary
        encoded = "01001000 01101001"
        solver = BinarySolver()
        candidates = solver.solve(encoded)
        assert candidates
        assert candidates[0].plaintext == "Hi"

    def test_decodes_continuous_binary(self):
        encoded = "0100100001101001"  # "Hi"
        solver = BinarySolver()
        candidates = solver.solve(encoded)
        assert candidates
        assert candidates[0].plaintext == "Hi"

    def test_non_binary_returns_empty(self):
        solver = BinarySolver()
        candidates = solver.solve("12345678")
        assert candidates == []

    def test_can_handle_spaced(self):
        solver = BinarySolver()
        assert solver.can_handle("01001000 01101001") is True

    def test_non_multiple_of_8_returns_empty(self):
        solver = BinarySolver()
        assert solver.can_handle("010010001") is False  # 9 bits


class TestMorseSolver:
    def test_decodes_simple_sos(self):
        solver = MorseSolver()
        candidates = solver.solve("... --- ...")
        assert candidates
        assert candidates[0].plaintext == "SOS"

    def test_decodes_hello(self):
        solver = MorseSolver()
        # H=...., E=., L=.-.., L=.-.., O=---
        morse = ".... . .-.. .-.. ---"
        candidates = solver.solve(morse)
        assert candidates
        assert candidates[0].plaintext == "HELLO"

    def test_decodes_multiword(self):
        solver = MorseSolver()
        morse = ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
        candidates = solver.solve(morse)
        assert candidates
        assert "HELLO" in candidates[0].plaintext
        assert "WORLD" in candidates[0].plaintext

    def test_invalid_morse_returns_empty(self):
        solver = MorseSolver()
        candidates = solver.solve("hello world")  # not morse
        assert candidates == []

    def test_can_handle_valid_morse(self):
        solver = MorseSolver()
        assert solver.can_handle(".- -...") is True


class TestUrlSolver:
    def test_decodes_url_encoding(self):
        solver = UrlSolver()
        candidates = solver.solve("Hello%20World%21")
        assert candidates
        assert any("Hello World!" in c.plaintext for c in candidates)

    def test_decodes_unicode_escape(self):
        solver = UrlSolver()
        # Actual \uXXXX escape sequences — solver must match _UNICODE_PATTERN
        candidates = solver.solve("\\u0048\\u0065\\u006c\\u006c\\u006f")
        assert candidates
        assert any("Hello" in c.plaintext for c in candidates)

    def test_no_encoding_returns_empty(self):
        solver = UrlSolver()
        candidates = solver.solve("plain text no encoding")
        assert candidates == []

    def test_can_handle_percent_encoded(self):
        solver = UrlSolver()
        assert solver.can_handle("%48%65%6c%6c%6f") is True
        assert solver.can_handle("no encoding here") is False

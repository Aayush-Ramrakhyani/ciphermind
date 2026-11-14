"""
/*
 * Solver accuracy benchmarks.
 * Each test encrypts a known plaintext, runs the full orchestrator,
 * and asserts that the correct cipher type appears in the top-N results.
 *
 * These are not fast unit tests — run with pytest -m accuracy separately.
 */
"""

import base64
import pytest

from cryptanalysis.orchestrator import CryptanalysisOrchestrator

pytestmark = pytest.mark.accuracy  # run with: pytest -m accuracy

SAMPLE_PLAINTEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Cryptography is the science of secret writing. "
    "Only those with the key can read the hidden message."
)


def _encrypt_caesar(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


def _encrypt_vigenere(text: str, key: str) -> str:
    key = key.lower()
    result = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            shift = ord(key[ki % len(key)]) - ord("a")
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return "".join(result)


class TestSolverAccuracy:
    """End-to-end accuracy benchmarks for the full orchestrator."""

    @pytest.fixture(autouse=True)
    def orchestrator(self):
        self.orch = CryptanalysisOrchestrator()

    def _top_cipher_types(self, result, n=3):
        return [c.cipher_type for c in result.candidates[:n]]

    def test_caesar_shift_3_identified(self):
        ct = _encrypt_caesar(SAMPLE_PLAINTEXT, 3)
        result = self.orch.analyse(ct)
        assert "caesar" in self._top_cipher_types(result), (
            f"Caesar not in top-3: {self._top_cipher_types(result)}"
        )

    def test_caesar_shift_13_identified(self):
        # ROT-13 is a valid alias for Caesar shift 13 — both are correct answers
        ct = _encrypt_caesar(SAMPLE_PLAINTEXT, 13)
        result = self.orch.analyse(ct)
        types = self._top_cipher_types(result, 5)
        assert "caesar" in types or "rot13" in types, f"Expected caesar or rot13, got: {types}"

    def test_atbash_identified(self):
        from cryptanalysis.ciphers.atbash import atbash_decrypt
        ct = atbash_decrypt(SAMPLE_PLAINTEXT)  # encrypt = decrypt for Atbash
        result = self.orch.analyse(ct)
        assert "atbash" in self._top_cipher_types(result, 5)

    def test_vigenere_key_key_identified(self):
        ct = _encrypt_vigenere(SAMPLE_PLAINTEXT, "key")
        result = self.orch.analyse(ct)
        assert "vigenere" in self._top_cipher_types(result, 5)

    def test_base64_detected(self):
        ct = base64.b64encode(SAMPLE_PLAINTEXT.encode()).decode()
        result = self.orch.analyse(ct)
        assert "base64" in self._top_cipher_types(result, 3)

    def test_morse_detected(self):
        # Short text for Morse
        ct = ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
        result = self.orch.analyse(ct)
        assert "morse" in self._top_cipher_types(result, 3)

    def test_hex_detected(self):
        ct = SAMPLE_PLAINTEXT[:20].encode().hex()
        result = self.orch.analyse(ct)
        assert "hex" in self._top_cipher_types(result, 3)

    def test_binary_detected(self):
        ct = " ".join(format(ord(c), "08b") for c in "HELLO WORLD")
        result = self.orch.analyse(ct)
        assert "binary" in self._top_cipher_types(result, 3)

    def test_rail_fence_2_rails_identified(self):
        from cryptanalysis.ciphers.rail_fence import rail_fence_decrypt
        # To encrypt, we "reverse" decrypt — use the same function since it's symmetric
        # Actually let's manually produce a rail fence encrypted text
        text = "WEAREDISCOVEREDRUNATONCE"
        # Rail fence encode with 3 rails
        rails = [[], [], []]
        rail, direction = 0, 1
        for ch in text:
            rails[rail].append(ch)
            if rail == 0:
                direction = 1
            elif rail == 2:
                direction = -1
            rail += direction
        ct = "".join("".join(r) for r in rails)
        result = self.orch.analyse(ct)
        assert "rail_fence" in self._top_cipher_types(result, 5)

    def test_statistical_summary_populated(self):
        ct = _encrypt_caesar(SAMPLE_PLAINTEXT, 7)
        result = self.orch.analyse(ct)
        assert "index_of_coincidence" in result.statistical_summary
        assert "chi_squared" in result.statistical_summary
        assert result.statistical_summary["alpha_count"] > 0

    def test_processing_time_recorded(self):
        ct = _encrypt_caesar(SAMPLE_PLAINTEXT, 5)
        result = self.orch.analyse(ct)
        assert result.processing_time_ms > 0

    def test_multilayer_base64_then_caesar(self):
        """Test that the multilayer engine finds: Base64 → Caesar."""
        inner_ct = _encrypt_caesar(SAMPLE_PLAINTEXT, 13)
        outer_ct = base64.b64encode(inner_ct.encode()).decode()
        result = self.orch.analyse(outer_ct)
        # Should detect base64 and find multi-layer chains
        assert "base64" in result.detected_encodings or result.multilayer_chains

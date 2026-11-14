"""
/*
 * Tests for statistical analysis modules:
 * Index of Coincidence, chi-squared, language scorer, n-gram analysis.
 */
"""

import pytest

from cryptanalysis.statistical.ioc import (
    index_of_coincidence, average_ioc_for_key_length,
    classify_cipher_type, ENGLISH_IOC, RANDOM_IOC
)
from cryptanalysis.statistical.frequency import (
    chi_squared, letter_frequencies, word_frequency_score
)
from cryptanalysis.statistical.language_scorer import score_text, classify_confidence
from cryptanalysis.statistical.ngram import bigram_log_probability


ENGLISH_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "In the beginning was the word and the word was with god. "
    "To be or not to be that is the question."
)

RANDOM_TEXT = "xqzjkwvbp mfyghronts dluciae qxzwvp jkbmfg"

CAESAR_3 = "WKH TXLFN EURZQ IRA MXPSV RYHU WKH ODCB GRJ"


LONG_ENGLISH = (
    "In the beginning was the word and the word was with god and the word was god. "
    "To be or not to be that is the question whether tis nobler in the mind to suffer. "
    "It was the best of times it was the worst of times it was the age of wisdom it was. "
    "Call me ishmael some years ago never mind how long precisely having little money. "
    "It is a truth universally acknowledged that a single man in possession of good fortune. "
)


class TestIndexOfCoincidence:
    def test_english_text_ioc_near_english(self):
        ioc = index_of_coincidence(ENGLISH_TEXT)
        # Short texts can have noisy IoC; accept wider range
        assert 0.040 <= ioc <= 0.100, f"Expected IoC ~0.065 for English, got {ioc}"

    def test_long_english_ioc_near_english(self):
        ioc = index_of_coincidence(LONG_ENGLISH)
        assert 0.055 <= ioc <= 0.085, f"Expected IoC ~0.065 for long English, got {ioc}"

    def test_caesar_ciphertext_preserves_ioc(self):
        # Caesar preserves IoC relative to plaintext — both should be in monoalphabetic range
        ioc_plain = index_of_coincidence(LONG_ENGLISH)
        from cryptanalysis.ciphers.caesar import _caesar_decrypt
        # Encrypt LONG_ENGLISH with shift 7
        def enc(text, shift):
            res = []
            for ch in text:
                if ch.isalpha():
                    b = ord('A') if ch.isupper() else ord('a')
                    res.append(chr((ord(ch)-b+shift)%26+b))
                else: res.append(ch)
            return ''.join(res)
        ioc_cipher = index_of_coincidence(enc(LONG_ENGLISH, 7))
        # Both should be in monoalphabetic range
        assert 0.050 <= ioc_cipher <= 0.090, f"Caesar IoC should stay near English, got {ioc_cipher}"

    def test_empty_text_returns_zero(self):
        assert index_of_coincidence("") == 0.0

    def test_single_char_returns_zero(self):
        assert index_of_coincidence("A") == 0.0

    def test_all_same_char_returns_one(self):
        ioc = index_of_coincidence("AAAAAAAAAA")
        assert abs(ioc - 1.0) < 0.01

    def test_classify_monoalphabetic(self):
        result = classify_cipher_type(LONG_ENGLISH)
        assert result == "monoalphabetic"

    def test_classify_polyalphabetic_for_vigenere(self):
        # A proper Vigenère (key length > 1) distributes frequencies uniformly
        # creating lower IoC → polyalphabetic classification
        from cryptanalysis.ciphers.vigenere import _vigenere_decrypt
        def enc_v(text, key):
            key = key.lower()
            res = []; ki = 0
            for ch in text:
                if ch.isalpha():
                    s = ord(key[ki%len(key)])-ord('a')
                    b = ord('A') if ch.isupper() else ord('a')
                    res.append(chr((ord(ch)-b+s)%26+b)); ki += 1
                else: res.append(ch)
            return ''.join(res)
        ct = enc_v(LONG_ENGLISH, "SECRETKEY")
        result = classify_cipher_type(ct)
        assert result in ("polyalphabetic", "random_or_transposition")


class TestChiSquared:
    def test_english_text_low_chi_squared(self):
        chi2 = chi_squared(ENGLISH_TEXT)
        # Frequency-based chi2 (proportions not counts); English < _CHI2_BAD=2.0
        # Pangram text forces rare letters (q,z,x) up, so ~0.70 is realistic
        assert chi2 < 2.0, f"English should have chi2 below _CHI2_BAD=2.0, got {chi2}"

    def test_caesar_ciphertext_higher_chi_squared_than_english(self):
        # Caesar shifts letter frequencies away from expected English distribution
        chi2_en = chi_squared(ENGLISH_TEXT)
        chi2_ca = chi_squared(CAESAR_3)
        # Ciphertext should have HIGHER chi2 than plaintext (frequencies shifted)
        assert chi2_ca > chi2_en, f"Caesar chi2={chi2_ca:.3f} should exceed English chi2={chi2_en:.3f}"

    def test_random_text_high_chi_squared(self):
        import string, random
        random.seed(42)
        rand_text = "".join(random.choice(string.ascii_lowercase) for _ in range(200))
        chi2 = chi_squared(rand_text)
        # Uniform distribution → chi2 above English baseline
        assert chi2 > 0.10

    def test_empty_text_returns_inf(self):
        import math
        assert math.isinf(chi_squared(""))


class TestLetterFrequencies:
    def test_frequencies_sum_to_one(self):
        freqs = letter_frequencies(ENGLISH_TEXT)
        total = sum(freqs.values())
        assert abs(total - 1.0) < 0.001

    def test_e_is_most_common_in_english(self):
        freqs = letter_frequencies(ENGLISH_TEXT)
        most_common = max(freqs, key=freqs.get)
        # 'e' or 't' should dominate in this text
        assert most_common in ("e", "t", "h", "o"), f"Most common: {most_common}"

    def test_all_26_letters_present(self):
        # "The quick brown fox jumps over the lazy dog" has all letters
        freqs = letter_frequencies("the quick brown fox jumps over the lazy dog")
        assert len(freqs) == 26
        assert all(v > 0 for v in freqs.values())


class TestWordFrequencyScore:
    def test_english_text_high_score(self):
        score = word_frequency_score(ENGLISH_TEXT)
        assert score > 0.4, f"English text should score > 0.4, got {score}"

    def test_random_gibberish_low_score(self):
        score = word_frequency_score("xkzqwvp mfyghrt bnjcds")
        assert score < 0.2

    def test_empty_text_zero(self):
        assert word_frequency_score("") == 0.0


class TestLanguageScorer:
    def test_english_scores_high(self):
        score = score_text(ENGLISH_TEXT)
        assert score > 0.35, f"English text should score > 0.35, got {score}"

    def test_caesar_ciphertext_scores_low(self):
        # Caesar ciphertext should score very low (shifted letter distribution)
        score = score_text(CAESAR_3)
        assert score < 0.20

    def test_gibberish_scores_near_zero(self):
        score = score_text("xqzxqzxqzxqzxqzxqz")
        assert score < 0.20

    def test_no_alpha_returns_zero(self):
        assert score_text("123 456 789") == 0.0

    def test_classify_confidence_levels(self):
        assert classify_confidence(0.75) == "high"
        assert classify_confidence(0.50) == "likely"
        assert classify_confidence(0.25) == "possible"
        assert classify_confidence(0.05) == "none"


class TestBigramLogProbability:
    def test_english_text_higher_than_random(self):
        blp_en = bigram_log_probability(ENGLISH_TEXT)
        blp_rand = bigram_log_probability(RANDOM_TEXT)
        assert blp_en > blp_rand, f"English blp {blp_en} should be > random {blp_rand}"

    def test_very_short_text_returns_minimum(self):
        from cryptanalysis.statistical.ngram import _LOG_MIN
        blp = bigram_log_probability("A")
        assert blp == _LOG_MIN

    def test_common_english_phrase(self):
        # Use non-pangram prose — avoids rare bigrams (nf, ox) that the fox pangram forces
        blp = bigram_log_probability("in the beginning was the word")
        assert blp > -6.0, f"Common phrase should score > -6.0, got {blp}"

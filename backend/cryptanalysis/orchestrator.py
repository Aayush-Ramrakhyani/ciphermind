"""
/*
 * CipherMind Cryptanalysis Orchestrator
 * Drives the full analysis pipeline:
 *   1. Statistical pre-analysis (IoC, frequency, n-grams)
 *   2. Encoding detection
 *   3. All cipher solvers
 *   4. Candidate ranking
 *   5. Multi-layer search
 *
 * The AI explanation layer is handled separately by ai/orchestrator.py
 * so the cryptanalysis engine remains independent of any API keys.
 */
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from cryptanalysis.base import AnalysisResult, CipherCandidate, ConfidenceLevel
from cryptanalysis.ciphers.affine import AffineSolver
from cryptanalysis.ciphers.atbash import AtbashSolver
from cryptanalysis.ciphers.caesar import CaesarSolver
from cryptanalysis.ciphers.columnar import ColumnarSolver
from cryptanalysis.ciphers.monoalphabetic import MonoalphabeticSolver
from cryptanalysis.ciphers.playfair import PlayfairSolver
from cryptanalysis.ciphers.rail_fence import RailFenceSolver
from cryptanalysis.ciphers.rot_variants import RotVariantsSolver
from cryptanalysis.ciphers.vigenere import VigenereSolver
from cryptanalysis.encodings.base64_codec import Base64Solver
from cryptanalysis.encodings.binary_codec import BinarySolver
from cryptanalysis.encodings.hex_codec import HexSolver
from cryptanalysis.encodings.morse_codec import MorseSolver
from cryptanalysis.encodings.url_codec import UrlSolver
from cryptanalysis.scoring.candidate_ranker import rank_candidates
from cryptanalysis.search.search_engine import MultiLayerSearchEngine
from cryptanalysis.statistical.frequency import chi_squared, letter_frequencies
from cryptanalysis.statistical.ioc import classify_cipher_type, index_of_coincidence
from cryptanalysis.statistical.ngram import bigram_log_probability, repeated_sequence_analysis

logger = logging.getLogger(__name__)


class CryptanalysisOrchestrator:
    """Main entry point for analysing an unknown ciphertext."""

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        cfg = settings or {}
        mono_iter = cfg.get("MONO_MAX_ITERATIONS", 10000)
        playfair_iter = cfg.get("PLAYFAIR_MAX_ITERATIONS", 5000)
        vigenere_max_key = cfg.get("VIGENERE_MAX_KEY_LEN", 20)
        self.multilayer_max_depth = cfg.get("MULTILAYER_MAX_DEPTH", 3)
        self.candidate_top_n = cfg.get("CANDIDATE_TOP_N", 5)

        self._cipher_solvers = [
            RotVariantsSolver(),
            AtbashSolver(),
            CaesarSolver(),
            AffineSolver(),
            RailFenceSolver(),
            ColumnarSolver(),
            VigenereSolver(max_key_len=vigenere_max_key),
            MonoalphabeticSolver(max_iterations=mono_iter),
            PlayfairSolver(max_iter=playfair_iter),
        ]
        self._encoding_solvers = [
            Base64Solver(),
            HexSolver(),
            BinarySolver(),
            MorseSolver(),
            UrlSolver(),
        ]

        # Build transform adapters for multi-layer search
        def _encoding_transforms(text: str) -> List[Tuple[str, Any, str]]:
            results = []
            for solver in self._encoding_solvers:
                if not solver.can_handle(text):
                    continue
                for c in solver.solve(text):
                    results.append((solver.name, c.key, c.plaintext))
            return results

        def _simple_cipher_transforms(text: str) -> List[Tuple[str, Any, str]]:
            results = []
            # Only light solvers in multilayer (ROT, Atbash, Caesar) to keep search tractable
            for solver in [RotVariantsSolver(), AtbashSolver(), CaesarSolver()]:
                if not solver.can_handle(text):
                    continue
                for c in solver.solve(text):
                    results.append((solver.name, c.key, c.plaintext))
            return results

        self._search_engine = MultiLayerSearchEngine(
            transforms=[_encoding_transforms, _simple_cipher_transforms],
            max_depth=self.multilayer_max_depth,
        )

    def analyse(self, ciphertext: str) -> AnalysisResult:
        """Run full analysis and return an AnalysisResult."""
        start = time.monotonic()
        result = AnalysisResult(ciphertext=ciphertext)

        # ── 1. Statistical pre-analysis ──────────────────────────────────────
        result.statistical_summary = self._statistical_summary(ciphertext)

        # ── 2. Encoding detection ─────────────────────────────────────────────
        all_candidates: List[CipherCandidate] = []
        detected_encodings = []
        for solver in self._encoding_solvers:
            if solver.can_handle(ciphertext):
                try:
                    candidates = solver.solve(ciphertext)
                    if candidates:
                        detected_encodings.append(solver.name)
                        all_candidates.extend(candidates)
                except Exception as exc:
                    logger.warning("Encoding solver %s failed: %s", solver.name, exc)

        result.detected_encodings = detected_encodings

        # ── 3. Cipher solvers ─────────────────────────────────────────────────
        ioc_type = result.statistical_summary.get("cipher_type_hint", "unknown")
        for solver in self._cipher_solvers:
            if not solver.can_handle(ciphertext):
                continue
            # Skip heavy solvers on very short text
            if len(ciphertext) < 10 and solver.name in ("vigenere", "playfair", "monoalphabetic"):
                continue
            try:
                candidates = solver.solve(ciphertext)
                all_candidates.extend(candidates)
            except Exception as exc:
                logger.warning("Cipher solver %s failed: %s", solver.name, exc)

        # ── 4. Rank candidates ────────────────────────────────────────────────
        ranked = rank_candidates(all_candidates, top_n=self.candidate_top_n * 3)
        result.candidates = self._deduplicate(ranked, top_n=self.candidate_top_n)

        # ── 5. Multi-layer search ─────────────────────────────────────────────
        try:
            chains = self._search_engine.search(ciphertext)
            result.multilayer_chains = [chain.to_dict() for chain in chains]
        except Exception as exc:
            logger.warning("Multi-layer search failed: %s", exc)

        result.processing_time_ms = round((time.monotonic() - start) * 1000)
        return result

    @staticmethod
    def _deduplicate(candidates: List[CipherCandidate], top_n: int) -> List[CipherCandidate]:
        """Remove candidates whose plaintext is identical to a higher-ranked candidate."""
        seen_texts: set = set()
        unique: List[CipherCandidate] = []
        for c in candidates:
            # Normalise: strip, uppercase, collapse whitespace for comparison
            normalised = " ".join(c.plaintext.upper().split())
            if normalised in seen_texts:
                continue
            seen_texts.add(normalised)
            unique.append(c)
            if len(unique) >= top_n:
                break
        return unique

    @staticmethod
    def _statistical_summary(ciphertext: str) -> Dict[str, Any]:
        """Compute all statistical features of the ciphertext."""
        ioc = index_of_coincidence(ciphertext)
        chi2 = chi_squared(ciphertext)
        blp = bigram_log_probability(ciphertext)
        freq = letter_frequencies(ciphertext)
        cipher_type_hint = classify_cipher_type(ciphertext)
        repeated = repeated_sequence_analysis(ciphertext)
        alpha_count = sum(1 for c in ciphertext if c.isalpha())

        return {
            "length": len(ciphertext),
            "alpha_count": alpha_count,
            "index_of_coincidence": round(ioc, 4),
            "chi_squared": round(chi2, 4),
            "bigram_log_probability": round(blp, 4),
            "letter_frequencies": {k: round(v, 4) for k, v in sorted(freq.items(), key=lambda x: -x[1])[:10]},
            "cipher_type_hint": cipher_type_hint,
            "repeated_sequences_count": len(repeated),
            "top_repeated_sequences": sorted(
                [(k, v) for k, v in repeated.items() if len(k) >= 3],
                key=lambda x: -x[1],
            )[:5],
        }

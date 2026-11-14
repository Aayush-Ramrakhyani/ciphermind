# CipherMind — Project Decisions

## Architecture Decisions

### AD-001: Cryptanalysis Engine Decoupled from Django
**Decision**: The entire `cryptanalysis/` and `ai/` packages have zero Django imports.
**Rationale**: Allows the engine to be tested without a database, run as a CLI tool, and reused in future projects. All Django-specific code lives in `apps/`.
**Trade-off**: Requires the Celery task to wire them together; slightly more code than embedding in views.

### AD-002: Simulated Annealing for Monoalphabetic and Playfair
**Decision**: Use simulated annealing (not pure hill-climbing) for monoalphabetic and Playfair solvers.
**Rationale**: Hill-climbing gets trapped in local optima. SA with a cooling schedule escapes local optima at acceptable cost (10K–50K iterations).
**Trade-off**: Non-deterministic results; test suite checks score threshold rather than exact plaintext.

### AD-003: Bounded DFS for Multi-layer Search
**Decision**: Max depth 3, min intermediate score 0.10 (pruning threshold).
**Rationale**: Depth 3 covers practically all real-world multi-layer encodings (Base64 → Caesar → plaintext). Score pruning makes the search tractable. Unbounded search would be O(solvers^depth).
**Trade-off**: May miss very unusual chains (depth > 3), but those are extremely rare in practice.

### AD-004: AI Layer is Optional Null Object
**Decision**: `get_provider()` returns a `BaseAIProvider` (null object) when no API key is set.
**Rationale**: The cryptanalysis engine must work offline and without paying for AI on every request. AI is an enrichment, not a core dependency.
**Trade-off**: Two code paths to test, but the null object pattern keeps the calling code clean.

### AD-005: Scoring Weights (0.35 chi² + 0.45 bigram + 0.20 word)
**Decision**: Bigrams carry the most weight.
**Rationale**: Bigram log-probability is robust across text lengths and captures sequential letter patterns that chi² misses. Word frequency is valuable for validation but can fail on proper nouns / specialized vocabulary.
**Trade-off**: Can be tuned; initial weights chosen empirically.

### AD-006: Vigenère Key Length — Kasiski + IoC Combined
**Decision**: Merge Kasiski test results and IoC-per-column results, deduplicate, test top-8.
**Rationale**: Either method alone can fail; the combination is more robust especially for short texts where Kasiski finds few repeated sequences.
**Trade-off**: Tests 8 key lengths per cipher — doubles Vigenère solver time.

### AD-007: Celery for Async Analysis
**Decision**: Analysis runs in Celery workers, not Django request threads.
**Rationale**: Monoalphabetic SA + Playfair SA can take 10–30 seconds. Blocking request threads would exhaust the WSGI worker pool. Celery with Redis broker scales horizontally.
**Trade-off**: Adds Redis + Celery infrastructure dependency; playground endpoint bypasses this for quick <1000 char interactive use.

### AD-008: UUID Primary Keys
**Decision**: All models use `UUIDField(primary_key=True)`.
**Rationale**: Prevents sequential ID enumeration (IDOR attack surface). UUIDs are unguessable.
**Trade-off**: Slightly larger indexes; no meaningful drawback for this scale.

### AD-009: `claude-opus-4-8` as Default AI Model
**Decision**: AI explanation uses `claude-opus-4-8` with `thinking: {type: "adaptive"}`.
**Rationale**: Cryptanalysis explanation requires mathematical reasoning. Adaptive thinking produces higher-quality cryptographic reasoning at acceptable latency. Streaming used to handle the 30+ second thinking window.
**Trade-off**: Higher cost per analysis than Haiku/Sonnet. Users can override via `ANTHROPIC_MODEL` env var.

### AD-010: Playground Endpoint (Synchronous, 1000-char Limit)
**Decision**: `/api/v1/playground/` runs synchronously in-process (no Celery), limited to 1000 chars.
**Rationale**: Interactive exploration needs sub-second feedback. 1000 chars is enough for most cipher examples. Heavy solvers (Playfair, monoalphabetic SA) are excluded from playground to keep latency < 200ms.
**Trade-off**: No persistence; not suitable for long messages.

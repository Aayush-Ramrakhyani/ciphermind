# CipherMind Architecture

## System Overview

CipherMind is a layered platform consisting of:

1. **Cryptanalysis Engine** — pure Python, no Django dependency, fully testable standalone
2. **Django REST API** — async job management, auth, rate limiting
3. **Celery Worker** — background analysis execution
4. **AI Integration** — optional Claude claude-opus-4-8 reasoning layer
5. **Flutter Frontend** — cross-platform client
6. **Infrastructure** — PostgreSQL, Redis, Docker

---

## Directory Structure

```
ciphermind/
├── backend/
│   ├── ciphermind/           Django project (settings, urls, middleware)
│   ├── apps/
│   │   ├── accounts/         Custom User model, JWT auth views
│   │   └── analysis/         AnalysisJob + AnalysisResult models, Celery tasks, API views
│   ├── cryptanalysis/        CORE ENGINE — no Django dependency
│   │   ├── base.py           CipherCandidate, AnalysisResult, BaseSolver dataclasses
│   │   ├── orchestrator.py   Main analysis pipeline coordinator
│   │   ├── ciphers/          9 classical cipher solvers
│   │   ├── encodings/        5 encoding detectors/decoders
│   │   ├── statistical/      IoC, chi², n-gram, language scorer
│   │   ├── scoring/          Candidate deduplication and ranking
│   │   └── search/           Multi-layer DFS transformation search
│   └── ai/
│       ├── provider.py       Factory + null-object base provider
│       ├── providers/        AnthropicProvider (claude-opus-4-8)
│       └── orchestrator.py   Enriches AnalysisResult with AI explanation
├── frontend/                 Flutter app
├── docker/                   Dockerfiles, nginx config
└── docs/                     This documentation
```

---

## Cryptanalysis Pipeline

```
Input ciphertext
       │
       ▼
┌──────────────────────┐
│  Statistical Summary │ — IoC, chi², bigram log-prob, letter frequencies
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Encoding Detection  │ — Base64, Hex, Binary, Morse, URL/Unicode
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│   Cipher Solvers     │ — All 9 classical ciphers (brute force + hill-climbing)
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Candidate Ranker    │ — Deduplicate, score, return top-N
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Multi-layer Search  │ — DFS up to depth 3 (Base64 → Caesar, etc.)
└──────────────────────┘
       │
       ▼
┌──────────────────────┐  if ANTHROPIC_API_KEY configured
│  AI Explanation      │ — Claude claude-opus-4-8 reasoning overlay
└──────────────────────┘
       │
       ▼
    AnalysisResult
```

---

## Cipher Solver Strategies

| Cipher | Strategy | Key Space |
|--------|----------|-----------|
| Caesar | Brute force all 26 shifts | 26 |
| ROT variants | Direct transforms (ROT5/13/18/47) | 4 |
| Atbash | Direct transform (self-inverse) | 1 |
| Affine | Brute force 12×26=312 valid keys | 312 |
| Rail Fence | Brute force 2–12 rails | 11 |
| Columnar | Brute force permutations ≤7!, greedy for >7 cols | Variable |
| Vigenère | Kasiski test + IoC-per-column → frequency per column | Auto-detected |
| Monoalphabetic | Simulated annealing on key letter pairs | 26! |
| Playfair | Simulated annealing on 5×5 key square | 25! |

---

## Scoring Function

The language scorer combines three signals:

```
score = 0.35 × chi_score + 0.45 × bigram_score + 0.20 × word_score
```

- **chi_score**: 1 - clamp(χ²/0.80) — lower χ² = more English-like letter distribution
- **bigram_score**: scaled bigram log-probability [−8.0, −2.5] → [0.0, 1.0]
- **word_score**: fraction of tokens that are common English words

Confidence levels: HIGH ≥ 0.70, LIKELY ≥ 0.45, POSSIBLE ≥ 0.20, NONE < 0.20

---

## API Design

### Auth Flow
```
POST /api/v1/auth/register/   → {user, tokens{access, refresh}}
POST /api/v1/auth/login/      → {access, refresh}
POST /api/v1/auth/token/refresh/ → {access}
POST /api/v1/auth/logout/     → blacklists refresh token
```

### Analysis Flow
```
POST /api/v1/analysis/        → 202 Accepted {id, status:"pending"}
GET  /api/v1/analysis/{id}/   → {id, status, result:{candidates, stats, ai_explanation}}
GET  /api/v1/analysis/list/   → paginated job history
POST /api/v1/playground/      → 200 inline result (max 1000 chars, sync)
```

### IDOR Prevention
Every queryset filters by `request.user`. UUID primary keys prevent enumeration.

---

## Database Schema

```sql
accounts_user       id UUID PK, email UNIQUE, api_tier, total_analyses
analysis_job        id UUID PK, user FK, ciphertext, ciphertext_hash, status, celery_task_id
analysis_result     id UUID PK, job FK UNIQUE, candidates JSONB, statistical_summary JSONB, ai_explanation TEXT
```

---

## AI Integration

Provider abstraction allows the app to work without an API key:

```python
provider = get_provider(settings)  # → AnthropicProvider or BaseAIProvider (null object)
ai_orch = AIOrchestrator(provider)
enriched_result = ai_orch.enrich(result)
```

The `AnthropicProvider` calls `claude-opus-4-8` with:
- `thinking: {type: "adaptive"}` for complex reasoning
- Streaming via `.stream()` context manager to avoid timeouts
- Input capped at 8000 chars to stay within context limits

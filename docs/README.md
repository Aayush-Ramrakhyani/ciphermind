# CipherMind

**Intelligent Autonomous Cryptanalysis Platform**

CipherMind autonomously analyses unknown encrypted messages, identifies possible encryption techniques, recovers likely plaintext, and explains the mathematical reasoning behind its conclusions.

---

## Features

- **9 Classical Cipher Solvers**: Caesar, ROT variants, Atbash, Affine, Rail Fence, Columnar Transposition, Vigenère, Monoalphabetic Substitution, Playfair
- **5 Encoding Detectors**: Base64, Hexadecimal, Binary, Morse Code, URL/Unicode Encoding
- **Statistical Analysis**: Letter frequency, Index of Coincidence, N-gram scoring, Kasiski examination
- **Multi-layer Detection**: Automatically finds chained encodings (e.g. Base64 → Caesar)
- **AI Reasoning**: Optional Claude claude-opus-4-8 integration for mathematical explanations
- **REST API**: JWT-authenticated, rate-limited, async analysis via Celery
- **Flutter Frontend**: Cross-platform client with dark+cyan design

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- (Optional) Anthropic API key for AI explanations

### Development

```bash
cd ciphermind

# Copy environment template
cp backend/.env.example backend/.env
# Edit backend/.env — set SECRET_KEY and optionally ANTHROPIC_API_KEY

# Start all services
docker-compose -f docker-compose.dev.yml up

# Run migrations (first time)
docker-compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

API available at `http://localhost:8000/api/v1/`
API docs at `http://localhost:8000/api/docs/`

### Production

```bash
cp backend/.env.example backend/.env
# Set SECRET_KEY, DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY, CORS_ALLOWED_ORIGINS

docker-compose up -d
```

---

## Running Tests

```bash
cd backend

# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests (excluding slow accuracy benchmarks)
pytest tests/ -v -m "not accuracy"

# Run accuracy benchmarks separately
pytest tests/benchmarks/ -v -m accuracy

# Run with coverage
pytest tests/ --cov=. --cov-report=html -m "not accuracy"
```

---

## API Reference

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"you","password":"SecurePass123!","password2":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass123!"}'
```

### Analysis

```bash
# Submit analysis
curl -X POST http://localhost:8000/api/v1/analysis/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"ciphertext":"KHOOR ZRUOG"}'
# Returns: {"id":"<job_uuid>","status":"pending",...}

# Poll for result
curl http://localhost:8000/api/v1/analysis/<job_uuid>/ \
  -H "Authorization: Bearer <access_token>"

# Interactive playground (sync, max 1000 chars)
curl -X POST http://localhost:8000/api/v1/playground/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"ciphertext":"KHOOR ZRUOG"}'
```

---

## Configuration

Key environment variables (see `backend/.env.example` for full list):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | Django secret key (50+ chars required) |
| `ANTHROPIC_API_KEY` | (empty) | Claude API key — AI disabled if not set |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | Model for AI explanations |
| `MAX_CIPHERTEXT_LENGTH` | `50000` | Max input chars |
| `ANALYSIS_TIMEOUT_SECONDS` | `120` | Celery task soft timeout |

---

## Architecture

See [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for the full pipeline diagram, solver strategies, and design decisions.

---

## Security

See [`docs/SECURITY_AUDIT.md`](SECURITY_AUDIT.md) for the full 19-point security checklist and threat model.

---
## License

MIT License — see LICENSE file.

> **Note:** This project was built for practice and learning purposes.
> If you'd like to use it, adapt it, or collaborate, feel free to reach out:
> **aayushr7777@gmail.com**


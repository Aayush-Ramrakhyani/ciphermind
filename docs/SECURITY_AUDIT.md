# CipherMind Security Audit

## Security Checklist (All 19 Mandatory Checks)

| # | Control | Status | Implementation |
|---|---------|--------|----------------|
| 1 | JWT Authentication | ✅ | `rest_framework_simplejwt` with 30-min access tokens, 7-day refresh |
| 2 | Refresh token blacklisting | ✅ | `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True` |
| 3 | Rate limiting — API | ✅ | DRF throttling: 10/h anon, 60/h user (production). Nginx layer: 10r/s |
| 4 | Rate limiting — Auth | ✅ | Nginx `limit_req_zone` 5r/m on `/api/v1/auth/` |
| 5 | CORS whitelist | ✅ | `CORS_ALLOWED_ORIGINS` from env, never wildcard in production |
| 6 | Input validation — length | ✅ | `MAX_CIPHERTEXT_LENGTH=50000`, serializer validates, playground 1000 chars |
| 7 | Input validation — type | ✅ | DRF serializer with `CharField(min_length=1, max_length=50000)` |
| 8 | Parameterized queries | ✅ | Django ORM used throughout — no raw SQL anywhere |
| 9 | IDOR prevention | ✅ | All querysets filter by `request.user`; UUID PKs prevent enumeration |
| 10 | HTTPS enforcement | ✅ | `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000` in production |
| 11 | Security headers | ✅ | `SecurityHeadersMiddleware` + nginx: X-Frame-Options DENY, X-Content-Type-Options nosniff, CSP, Referrer-Policy |
| 12 | CSRF protection | ✅ | Django CSRF middleware; API uses JWT Bearer (not cookies) |
| 13 | Audit logging | ✅ | `AuditLogMiddleware` logs all mutating API calls with user_id, IP, path |
| 14 | Password validation | ✅ | 10-char minimum, similarity, common-password, numeric validators |
| 15 | Sensitive env secrets | ✅ | All secrets in env vars; `.env.example` committed, `.env` gitignored |
| 16 | Dependency security scan | ✅ | `bandit` (SAST) + `safety` (CVE scan) in CI |
| 17 | Max concurrent analyses | ✅ | Per-user cap: `MAX_CONCURRENT_ANALYSES=5` before accepting new jobs |
| 18 | Celery task timeouts | ✅ | `CELERY_TASK_SOFT_TIME_LIMIT=120s`, hard limit 150s |
| 19 | Secret key minimum length | ✅ | Settings doc requires 50+ chars; dev key is insecure-clearly-labelled |

---

## Threat Model

### Attack Vectors Considered

**Authentication & Authorization**
- Brute-force login → rate limited 5/min per IP at nginx layer
- Token theft → short 30-min access tokens; refresh rotation invalidates stolen refresh tokens
- IDOR — accessing another user's jobs → all querysets filtered by `user=request.user`
- Privilege escalation → `api_tier` field cannot be self-modified (read-only in serializer)

**Injection**
- SQL injection → Django ORM with parameterized queries; zero raw SQL
- Command injection → no shell calls anywhere in cryptanalysis engine
- XSS → DRF returns JSON only; CSP header restricts script execution

**Denial of Service**
- Large input flood → 50K char limit enforced at serializer level
- Concurrent job flooding → per-user concurrent cap (5 jobs)
- Algorithmic DoS → Celery 120s soft timeout; heavy solvers (Playfair, monoalphabetic) can be disabled per tier

**AI Layer**
- Prompt injection in ciphertext → AI prompt uses fixed system message; user data is in `content` only, not system
- API key exposure → key in env var, never logged, never returned to client

---

## Dependency Audit

Run regularly:
```bash
# CVE scan
safety check -r requirements.txt

# SAST
bandit -r cryptanalysis ai apps -ll

# Check for outdated packages
pip list --outdated
```

---

## Penetration Testing Notes

The following endpoints require testing before production deployment:

1. **IDOR probe**: Create Job with User A, attempt GET with User B's JWT → must return 404
2. **SQL injection**: Submit `'; DROP TABLE analysis_job; --` as ciphertext → must succeed as plain text
3. **Rate limit enforcement**: Submit 15 analysis requests in 1 hour → 11th+ must return 429
4. **JWT replay**: Use blacklisted refresh token → must return 401
5. **Oversized input**: Submit 50001 chars → must return 400
6. **Null bytes**: Submit `\x00\x00\x00` → must not crash server (500)

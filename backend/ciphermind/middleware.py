"""
/*
 * CipherMind custom middleware:
 * SecurityHeadersMiddleware — adds hardening headers on every response.
 * AuditLogMiddleware — logs all mutating API calls for IDOR/abuse tracking.
 */
"""

import json
import logging
import time
import uuid

logger = logging.getLogger("audit")


class SecurityHeadersMiddleware:
    """Add security headers on every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        )
        return response


class AuditLogMiddleware:
    """Emit a structured audit log entry for every mutating API call."""

    MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in self.MUTATING_METHODS or not request.path.startswith("/api/"):
            return self.get_response(request)

        request_id = str(uuid.uuid4())
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000)

        user_id = getattr(request.user, "id", None)
        logger.info(
            "api_call",
            extra={
                "request_id": request_id,
                "user_id": str(user_id) if user_id else "anonymous",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "ip": self._get_client_ip(request),
            },
        )
        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

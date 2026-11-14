"""CipherMind development settings — relaxed security for local work."""

from .base import *  # noqa: F401, F403

DEBUG = True
SECRET_KEY = "dev-only-insecure-secret-key-do-not-use-in-production-ever"

ALLOWED_HOSTS = ["*"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
]

try:
    import django_extensions  # noqa: F401
    INSTALLED_APPS += ["django_extensions"]  # noqa: F405
except ImportError:
    pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "cryptanalysis": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "ai": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

DATABASES["default"]["HOST"] = "localhost"  # noqa: F405

"""Celery application configuration for CipherMind."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciphermind.settings.development")

app = Celery("ciphermind")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

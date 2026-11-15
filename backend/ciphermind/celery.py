"""
/*
 * Celery application configuration for CipherMind.
 * Tasks are auto-discovered from each installed app's tasks.py.
 */
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciphermind.settings.development")

app = Celery("ciphermind")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

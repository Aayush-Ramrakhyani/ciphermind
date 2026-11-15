"""
/*
 * Django app config for the analysis app.
 */
"""

from django.apps import AppConfig


class AnalysisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analysis"
    label = "analysis"

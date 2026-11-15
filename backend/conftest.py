"""
/*
 * Global pytest configuration and shared fixtures.
 * Sets DJANGO_SETTINGS_MODULE to development before Django is imported.
 */
"""

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciphermind.settings.development")


@pytest.fixture(scope="session")
def django_db_setup():
    pass


@pytest.fixture
def db_setup(transactional_db):
    pass

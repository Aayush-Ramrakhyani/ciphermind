"""Global pytest configuration and fixtures."""

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

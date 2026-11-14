"""
/*
 * Custom User model — extends AbstractUser with rate-limit and
 * API-access tier fields.
 */
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    # API tier controls per-user rate limits
    api_tier = models.CharField(
        max_length=20,
        choices=[("free", "Free"), ("pro", "Pro"), ("admin", "Admin")],
        default="free",
    )
    total_analyses = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "accounts_user"
        indexes = [models.Index(fields=["email"])]

    def __str__(self) -> str:
        return self.email

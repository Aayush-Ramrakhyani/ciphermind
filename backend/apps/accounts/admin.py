"""
/*
 * Django admin registration for the custom User model.
 * Extends the default UserAdmin with CipherMind-specific fields.
 */
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "api_tier", "total_analyses", "is_active", "date_joined")
    list_filter = ("api_tier", "is_active", "is_staff")
    search_fields = ("email", "username")
    ordering = ("-date_joined",)
    fieldsets = UserAdmin.fieldsets + (
        ("CipherMind", {"fields": ("api_tier", "total_analyses")}),
    )

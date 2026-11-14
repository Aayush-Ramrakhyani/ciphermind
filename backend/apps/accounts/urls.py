"""Accounts URL patterns."""

from django.urls import path

from .views import ProfileView

urlpatterns = [
    path("auth/profile/", ProfileView.as_view(), name="profile"),
]

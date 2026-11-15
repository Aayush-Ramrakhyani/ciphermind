"""
/*
 * Accounts URL patterns.
 * Auth routes (register/login/logout/token-refresh) are wired at root urls.py;
 * only the profile endpoint lives here.
 */
"""

from django.urls import path

from .views import ProfileView

urlpatterns = [
    path("auth/profile/", ProfileView.as_view(), name="profile"),
]

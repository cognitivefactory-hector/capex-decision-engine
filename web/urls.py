"""URL routes for the web layer.

The Projects / Risk / Portfolio tabs (SPEC §4.3) land in later milestones; M0
serves only the landing page.
"""
from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
]

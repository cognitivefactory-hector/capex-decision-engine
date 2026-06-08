"""URL routes for the web layer (SPEC §4.3: Projects / Risk / Portfolio)."""
from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    path("", views.home, name="home"),
    path("projects/", views.projects, name="projects"),
    path("risk/", views.risk, name="risk"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("portfolio/optimize/", views.optimize, name="optimize"),
    path("portfolio/memo/", views.memo, name="memo"),
]

"""View layer — thin. All numbers come from the framework-free ``engine`` package."""
from django.shortcuts import render


def home(request):
    """Landing page. Tabs are stubbed until their milestones (SPEC §4.3)."""
    return render(request, "web/home.html")

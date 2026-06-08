"""View layer — thin. All numbers come from the framework-free ``engine`` package
via ``web.services``. The optimizer decides; the LLM only explains."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import services


def healthz(request):
    """Liveness probe for the host (no heavy work — does not run the simulation)."""
    return HttpResponse("ok", content_type="text/plain")


def _budget_lambda(request: HttpRequest) -> tuple[float, float]:
    source = request.POST if request.method == "POST" else request.GET
    try:
        budget = float(source.get("budget", services.DEFAULT_BUDGET))
    except (TypeError, ValueError):
        budget = services.DEFAULT_BUDGET
    try:
        risk_aversion = float(source.get("lam", services.DEFAULT_LAMBDA))
    except (TypeError, ValueError):
        risk_aversion = services.DEFAULT_LAMBDA
    return budget, risk_aversion


def home(request):
    """Landing page."""
    return render(request, "web/home.html", {"active": "home"})


def projects(request):
    """Projects tab: intake corpus + deterministic metrics table."""
    return render(
        request, "web/projects.html",
        {"active": "projects", "rows": services.projects_table()},
    )


def risk(request):
    """Risk tab: NPV distributions + tornado per project."""
    return render(
        request, "web/risk.html",
        {"active": "risk", "figures": services.risk_figures()},
    )


def _portfolio_payload(budget: float, risk_aversion: float) -> dict:
    portfolio, context = services.portfolio_context(budget, risk_aversion)
    return {
        "budget": budget,
        "lam": risk_aversion,
        "portfolio": portfolio,
        "context": context,
        "comparison": services.comparison_figure(context),
        "memo_available": services.memo_available(),
    }


def portfolio(request):
    """Portfolio tab: budget slider, funded-vs-cut, the cut project, the memo."""
    budget, risk_aversion = _budget_lambda(request)
    ctx = _portfolio_payload(budget, risk_aversion)
    ctx.update(
        active="portfolio",
        budget_min=services.BUDGET_MIN,
        budget_max=services.BUDGET_MAX,
    )
    return render(request, "web/portfolio.html", ctx)


def optimize(request):
    """HTMX partial: re-optimize for the current budget/lambda."""
    budget, risk_aversion = _budget_lambda(request)
    return render(request, "web/_portfolio_result.html", _portfolio_payload(budget, risk_aversion))


@require_POST
def memo(request):
    """HTMX partial: generate the grounded memo (one LLM call)."""
    budget, risk_aversion = _budget_lambda(request)
    if not services.memo_available():
        return render(request, "web/_memo.html", {"unavailable": True})
    try:
        generated = services.portfolio_memo(budget, risk_aversion)
    except Exception as exc:  # surface API failures without 500-ing the page
        return render(request, "web/_memo.html", {"error": str(exc)})
    return render(request, "web/_memo.html", {"memo": generated})

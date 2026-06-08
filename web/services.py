"""Service layer: the bridge between the pure ``engine`` and the Django views.

Everything expensive (the correlated Monte Carlo over the corpus) is computed
once and cached — it's deterministic under the fixed seed. The optimizer is
cheap, so the budget slider re-optimizes per request without re-simulating.

Plotly figures are rendered to HTML fragments here so the views and templates
stay thin. This module may use Django settings; ``engine`` never does.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import plotly.graph_objects as go
from django.conf import settings

from engine.data.projects import (
    WACC,
    EvaluatedProject,
    ProjectSpec,
    candidates,
    corpus,
    default_constraints,
    evaluate_corpus,
)
from engine.finance.metrics import (
    discounted_payback,
    irr,
    mirr,
    npv,
    payback,
    profitability_index,
)
from engine.memo.generate import build_context, generate_memo
from engine.memo.schemas import InvestmentMemo, MemoContext
from engine.optimizer.select import Portfolio, optimize
from engine.sensitivity.tornado import tornado

_FUNDED_COLOR = "#1f6feb"
_CUT_COLOR = "#c0392b"
_INK = "#13171f"

# Budget-slider bounds for the UI (total corpus capital is ~2700).
BUDGET_MIN = 400
BUDGET_MAX = 2700
DEFAULT_BUDGET = 1200.0
DEFAULT_LAMBDA = 1.0


# --- Cached, deterministic evaluation --------------------------------------

@lru_cache(maxsize=1)
def get_evaluated() -> tuple[EvaluatedProject, ...]:
    """The corpus run through the correlated Monte Carlo (computed once)."""
    return tuple(evaluate_corpus())


def _npvs_by_name() -> dict[str, np.ndarray]:
    return {e.spec.name: e.result.npvs for e in get_evaluated()}


# --- Deterministic per-project metrics (Projects tab) ----------------------

def deterministic_metrics(spec: ProjectSpec) -> dict:
    """NPV/IRR/payback/PI/MIRR at the mean of each uncertain input."""
    mean_sample = {name: dist.mean for name, dist in spec.inputs.items()}
    cf = spec.build_cashflows(mean_sample)
    return {
        "npv": npv(WACC, cf),
        "irr": irr(cf),
        "payback": payback(cf),
        "discounted_payback": discounted_payback(WACC, cf),
        "pi": profitability_index(WACC, cf),
        "mirr": mirr(cf, finance_rate=WACC, reinvest_rate=WACC),
    }


@lru_cache(maxsize=1)
def projects_table() -> list[dict]:
    """Rows for the Projects tab: identity + deterministic metrics + ranges."""
    rows = []
    for spec in corpus():
        ranges = {
            name: (getattr(d, "low", None), getattr(d, "mean", None), getattr(d, "high", None))
            for name, d in spec.inputs.items()
        }
        rows.append(
            {
                "name": spec.name,
                "kind": spec.kind,
                "capital": spec.capital,
                "horizon": spec.horizon,
                "rationale": spec.rationale,
                "metrics": deterministic_metrics(spec),
                "ranges": ranges,
            }
        )
    return rows


# --- Optimization (Portfolio tab; re-run per slider change) ----------------

def optimize_portfolio(budget: float, risk_aversion: float) -> Portfolio:
    cands = candidates(list(get_evaluated()))
    return optimize(cands, default_constraints(budget), risk_aversion=risk_aversion)


def portfolio_context(budget: float, risk_aversion: float) -> tuple[Portfolio, MemoContext]:
    """The optimizer result plus the grounded facts (reused for display + memo)."""
    evaluated = list(get_evaluated())
    portfolio = optimize_portfolio(budget, risk_aversion)
    projects = candidates(evaluated)
    metrics_by_name = {e.spec.name: e.result.metrics for e in evaluated}
    kinds_by_name = {e.spec.name: e.spec.kind for e in evaluated}
    context = build_context(
        portfolio, projects, metrics_by_name, kinds_by_name, default_constraints(budget)
    )
    return portfolio, context


# --- Memo (Portfolio tab; one LLM call) ------------------------------------

def portfolio_memo(
    budget: float, risk_aversion: float, *, client=None
) -> InvestmentMemo:
    """Generate the grounded memo for the current portfolio. The LLM explains;
    the optimizer already decided. ``client`` is injectable for tests."""
    _, context = portfolio_context(budget, risk_aversion)
    return generate_memo(context, client=client, model=settings.MEMO_MODEL)


def memo_available() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


# --- Plotly figures --------------------------------------------------------

def _fig_html(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})


def _layout(fig: go.Figure, *, height: int = 280, title: str = "") -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=40 if title else 16, b=32),
        showlegend=False,
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        font=dict(color=_INK, size=12),
        bargap=0.02,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef1f5", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef1f5", zeroline=False)
    return fig


def _distribution_fig(npvs: np.ndarray, metrics, *, title: str = "") -> go.Figure:
    """NPV distribution as a server-binned bar chart (light payload), with the
    loss line at 0, the mean, and the CVaR tail marked."""
    counts, edges = np.histogram(npvs, bins=48)
    centers = (edges[:-1] + edges[1:]) / 2
    colors = [_CUT_COLOR if c < 0 else _FUNDED_COLOR for c in centers]
    fig = go.Figure(go.Bar(x=centers, y=counts, marker_color=colors, marker_line_width=0))
    fig.add_vline(x=0, line_dash="dot", line_color="#888")
    fig.add_vline(x=float(metrics.mean), line_color=_INK, line_width=2,
                  annotation_text="mean", annotation_position="top")
    fig.add_vline(x=float(metrics.cvar), line_color=_CUT_COLOR, line_dash="dash",
                  annotation_text="CVaR", annotation_position="top")
    _layout(fig, title=title)
    fig.update_xaxes(title_text="NPV")
    fig.update_yaxes(title_text="frequency")
    return fig


def _tornado_fig(spec: ProjectSpec) -> go.Figure:
    """Floating-bar tornado: each input's NPV span across its P10–P90 band."""
    bars = tornado(spec.inputs, spec.build_cashflows, WACC)
    fig = go.Figure()
    for bar in reversed(bars):  # largest swing ends up on top
        lo, hi = sorted((bar.low_npv, bar.high_npv))
        fig.add_trace(
            go.Bar(
                y=[bar.input],
                x=[hi - lo],
                base=lo,
                orientation="h",
                marker_color=_FUNDED_COLOR,
                marker_line_width=0,
            )
        )
    if bars:
        fig.add_vline(x=float(bars[0].base_npv), line_color=_INK, line_dash="dot")
    _layout(fig, height=max(180, 60 + 36 * len(bars)))
    fig.update_xaxes(title_text="NPV")
    return fig


@lru_cache(maxsize=1)
def risk_figures() -> list[dict]:
    """Per-project distribution + tornado HTML fragments for the Risk tab."""
    npvs = _npvs_by_name()
    figs = []
    for e in get_evaluated():
        figs.append(
            {
                "name": e.spec.name,
                "kind": e.spec.kind,
                "metrics": e.result.metrics,
                "distribution": _fig_html(_distribution_fig(npvs[e.spec.name], e.result.metrics)),
                "tornado": _fig_html(_tornado_fig(e.spec)),
            }
        )
    return figs


def comparison_figure(context: MemoContext) -> str | None:
    """The money shot: the cut high-NPV trap's distribution beside the steadiest
    funded project's. Returns None if there's nothing cut to compare."""
    if context.cut_high_npv is None or not context.funded:
        return None
    npvs = _npvs_by_name()
    metrics = {e.spec.name: e.result.metrics for e in get_evaluated()}

    cut = context.cut_high_npv
    funded = min(context.funded, key=lambda f: f.cvar)  # the tightest downside we funded

    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"CUT: {cut.name} (E[NPV] {cut.expected_npv:.0f}, CVaR {cut.cvar:.0f})",
            f"FUNDED: {funded.name} (E[NPV] {funded.expected_npv:.0f}, CVaR {funded.cvar:.0f})",
        ),
    )
    for col, fact in ((1, cut), (2, funded)):
        data = npvs[fact.name]
        counts, edges = np.histogram(data, bins=48)
        centers = (edges[:-1] + edges[1:]) / 2
        colors = [_CUT_COLOR if c < 0 else _FUNDED_COLOR for c in centers]
        fig.add_trace(go.Bar(x=centers, y=counts, marker_color=colors, marker_line_width=0),
                      row=1, col=col)
        fig.add_vline(x=0, line_dash="dot", line_color="#888", row=1, col=col)
        fig.add_vline(x=float(metrics[fact.name].cvar), line_dash="dash",
                      line_color=_CUT_COLOR, row=1, col=col)
    _layout(fig, height=320)
    return _fig_html(fig)

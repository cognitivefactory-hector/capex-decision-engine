"""M7 — service layer (engine ↔ web bridge)."""
from types import SimpleNamespace

from engine.data.projects import TRAP_NAME
from engine.memo.schemas import InvestmentMemo
from web import services


def test_get_evaluated_is_cached_and_returns_corpus():
    a = services.get_evaluated()
    b = services.get_evaluated()
    assert len(a) == 8
    assert a is b  # lru_cache returns the same object


def test_deterministic_metrics_has_all_fields():
    from engine.data.projects import corpus

    m = services.deterministic_metrics(corpus()[0])
    assert set(m) == {"npv", "irr", "payback", "discounted_payback", "pi", "mirr"}
    assert m["pi"] > 0


def test_projects_table_has_one_row_per_project():
    rows = services.projects_table()
    assert len(rows) == 8
    assert all("metrics" in r for r in rows)


def test_low_risk_aversion_funds_the_trap():
    result = services.optimize_portfolio(services.DEFAULT_BUDGET, 0.0)
    assert TRAP_NAME in result.funded


def test_high_risk_aversion_cuts_the_trap():
    result = services.optimize_portfolio(services.DEFAULT_BUDGET, 1.0)
    assert TRAP_NAME in result.cut


def test_portfolio_context_surfaces_the_cut_trap():
    _, context = services.portfolio_context(services.DEFAULT_BUDGET, 1.0)
    assert context.cut_high_npv is not None
    assert context.cut_high_npv.name == TRAP_NAME


def test_comparison_figure_present_when_something_is_cut():
    _, context = services.portfolio_context(services.DEFAULT_BUDGET, 1.0)
    html = services.comparison_figure(context)
    assert html is not None
    assert "plotly" in html.lower()


def test_risk_figures_render_html_per_project():
    figs = services.risk_figures()
    assert len(figs) == 8
    assert all("plotly" in f["distribution"].lower() for f in figs)
    assert all("<div" in f["tornado"].lower() for f in figs)


def test_portfolio_memo_uses_injected_client_and_configured_model(settings):
    settings.MEMO_MODEL = "claude-sonnet-4-6"
    calls = []

    class _Msgs:
        def parse(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                parsed_output=InvestmentMemo(
                    summary="s", funded_rationale="f", cut_rationale="c", risk_note="r"
                )
            )

    client = SimpleNamespace(messages=_Msgs())
    memo = services.portfolio_memo(services.DEFAULT_BUDGET, 1.0, client=client)
    assert isinstance(memo, InvestmentMemo)
    assert calls[0]["model"] == "claude-sonnet-4-6"
    # The grounded numbers reach the model.
    user = calls[0]["messages"][0]["content"]
    assert TRAP_NAME in user

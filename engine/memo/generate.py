"""Build the grounded context and generate the memo.

``build_context`` is a pure function (no API). ``generate_memo`` takes an
optional ``client`` for dependency injection so it is unit-testable with a mock —
the API is never hit in tests. The model only explains; it never decides.

Default model is ``claude-sonnet-4-6`` per the M0 decision (DECISIONS.md): one
grounded-summarization call per portfolio, where Sonnet's quality is ample at
materially lower cost than Opus. Override via the ``model`` argument (the Django
layer passes ``settings.MEMO_MODEL``).
"""
from __future__ import annotations

from collections.abc import Mapping

from engine.montecarlo.risk import RiskMetrics
from engine.optimizer.select import Constraints, Portfolio, Project

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import InvestmentMemo, MemoContext, ProjectFact

DEFAULT_MEMO_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 2048


def build_context(
    portfolio: Portfolio,
    projects: list[Project],
    metrics_by_name: Mapping[str, RiskMetrics],
    kinds_by_name: Mapping[str, str],
    constraints: Constraints,
) -> MemoContext:
    """Assemble the grounded facts from already-computed results."""
    by_name = {p.name: p for p in projects}
    funded_names = set(portfolio.funded)

    def fact(name: str) -> ProjectFact:
        p = by_name[name]
        m = metrics_by_name[name]
        return ProjectFact(
            name=name,
            kind=kinds_by_name.get(name, name),
            cost=p.cost,
            expected_npv=p.expected_npv,
            p_loss=m.p_loss,
            cvar=m.cvar,
            downside=p.downside,
            score=portfolio.scores.get(name, 0.0),
            funded=name in funded_names,
        )

    funded = [fact(n) for n in portfolio.funded]
    cut = [fact(n) for n in portfolio.cut]
    cut_high_npv = max(cut, key=lambda f: f.expected_npv) if cut else None

    return MemoContext(
        budget=constraints.budget,
        risk_aversion=portfolio.risk_aversion,
        total_cost=portfolio.total_cost,
        objective=portfolio.objective,
        funded=funded,
        cut=cut,
        cut_high_npv=cut_high_npv,
        must_fund=sorted(constraints.must_fund),
    )


def generate_memo(
    context: MemoContext,
    *,
    client=None,
    model: str = DEFAULT_MEMO_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> InvestmentMemo:
    """Generate the grounded memo via the Anthropic Messages API.

    Pass ``client`` to inject a (real or fake) Anthropic client; when omitted a
    default ``anthropic.Anthropic()`` is constructed (reads ``ANTHROPIC_API_KEY``
    from the environment). The system prompt is cached; one call per portfolio.
    """
    if client is None:
        import anthropic

        client = anthropic.Anthropic()

    response = client.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": build_user_prompt(context)}],
        output_format=InvestmentMemo,
    )
    return response.parsed_output

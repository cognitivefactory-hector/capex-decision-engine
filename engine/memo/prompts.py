"""System prompt and the grounded user prompt.

The system prompt is the guardrail: the optimizer has ALREADY decided; the model
only explains, grounded strictly in the numbers it is given. The user prompt is
those numbers. This is the "the LLM never decides" invariant, enforced in text
(and asserted in tests).
"""
from __future__ import annotations

from .schemas import MemoContext, ProjectFact

SYSTEM_PROMPT = (
    "You write a short internal capital-allocation memo for a plant's finance and "
    "engineering partners.\n\n"
    "CRITICAL GROUND RULES:\n"
    "- A risk-adjusted portfolio optimizer has ALREADY made the funding decision. "
    "Your job is only to EXPLAIN that decision in clear prose.\n"
    "- Ground every statement strictly in the numbers provided below. Do not "
    "compute, re-rank, or invent figures. If a number is not provided, do not "
    "state it.\n"
    "- You do NOT choose, rank, recommend, or second-guess which projects to fund. "
    "Do not suggest alternative portfolios or changes. The decision is final.\n"
    "- Explicitly name and explain the highest-expected-NPV project that was CUT, "
    "using its downside tail (CVaR) and probability of loss — this is the point of "
    "the memo.\n"
    "- Be concise, concrete, and honest that these are estimates with ranges.\n\n"
    "This is an illustrative analysis on synthetic projects — not investment advice."
)


def _fmt(fact: ProjectFact) -> str:
    return (
        f"- {fact.name} ({fact.kind}): capital {fact.cost:.0f}, "
        f"E[NPV] {fact.expected_npv:.1f}, P(NPV<0) {fact.p_loss:.0%}, "
        f"CVaR {fact.cvar:.1f}, risk-adjusted score {fact.score:.1f}"
    )


def build_user_prompt(context: MemoContext) -> str:
    """Render the computed numbers the memo must be grounded in."""
    lines: list[str] = [
        "Decision parameters (already applied by the optimizer):",
        f"- Budget cap: {context.budget:.0f}",
        f"- Risk-aversion (lambda): {context.risk_aversion}",
        f"- Total capital committed: {context.total_cost:.0f}",
        f"- Portfolio objective (expected NPV - lambda*downside): {context.objective:.1f}",
        f"- Must-fund (compliance): {', '.join(context.must_fund) or 'none'}",
        "",
        "FUNDED projects (the optimizer's decision):",
        *[_fmt(f) for f in context.funded],
        "",
        "CUT projects (not funded):",
        *[_fmt(f) for f in context.cut],
    ]
    if context.cut_high_npv is not None:
        c = context.cut_high_npv
        lines += [
            "",
            "HIGHEST-EXPECTED-NPV PROJECT THAT WAS CUT (explain this prominently):",
            f"- {c.name} ({c.kind}): highest E[NPV] at {c.expected_npv:.1f}, but a fat "
            f"downside tail — CVaR {c.cvar:.1f}, P(NPV<0) {c.p_loss:.0%}. It was cut to "
            "hold the portfolio's downside, trading expected return for survivability.",
        ]
    lines += [
        "",
        "Write the memo explaining this decision. Do not change it.",
    ]
    return "\n".join(lines)

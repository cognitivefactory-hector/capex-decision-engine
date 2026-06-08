"""Memo data shapes.

``MemoContext`` / ``ProjectFact`` are the grounded facts handed to the model.
``InvestmentMemo`` is the structured output the model must return — it explains
the optimizer's decision in prose, nothing more.
"""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ProjectFact:
    """One project's computed numbers, as decided by the optimizer."""

    name: str
    kind: str
    cost: float
    expected_npv: float
    p_loss: float
    cvar: float
    downside: float
    score: float  # risk-adjusted value: expected_npv - lambda*downside
    funded: bool


@dataclass(frozen=True)
class MemoContext:
    """Everything the memo is grounded in — all of it already computed."""

    budget: float
    risk_aversion: float
    total_cost: float
    objective: float
    funded: list[ProjectFact]
    cut: list[ProjectFact]
    cut_high_npv: ProjectFact | None  # highest-E[NPV] project that was cut (the trap)
    must_fund: list[str]


class InvestmentMemo(BaseModel):
    """The model's structured output. Prose only — grounded in the numbers."""

    summary: str = Field(
        description="2-3 sentence executive summary of what was funded and the "
        "risk-adjusted rationale, grounded strictly in the provided numbers."
    )
    funded_rationale: str = Field(
        description="Why the funded set makes sense under the budget and "
        "constraints, citing the provided NPVs and downside figures."
    )
    cut_rationale: str = Field(
        description="Why projects were cut — especially the highest-expected-NPV "
        "project that was cut, naming it and citing its CVaR / downside tail."
    )
    risk_note: str = Field(
        description="The expected-return-vs-downside tradeoff at this risk-aversion "
        "level, grounded in the provided figures. Do not recommend changes."
    )

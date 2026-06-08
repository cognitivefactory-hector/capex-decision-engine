"""Budget-constrained, risk-adjusted portfolio selection — the decision.

For the handful of projects a capital cycle weighs (~5-8), we enumerate every
subset and keep the feasible one with the best risk-adjusted objective:

    maximize   Σ_{i in S} (expected_npv_i − λ · downside_i)
    subject to Σ cost_i ≤ budget, must-fund ⊆ S, at most one of each
               mutually-exclusive group, and every dependency satisfied.

Exhaustive search is chosen over MILP/pulp deliberately: at this scale it is
instant, always finds the true optimum, and — most importantly — every funded
and cut decision is fully explainable on a whiteboard. ``downside`` is a
non-negative risk penalty; the integration layer sets it to the expected
shortfall, ``max(0, −CVaR)`` (M2), so a fat negative tail raises the penalty.
λ (``risk_aversion``) is the documented, defensible knob that trades expected
return for a tighter downside — and at high λ it cuts the high-NPV trap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations


@dataclass(frozen=True)
class Project:
    name: str
    cost: float
    expected_npv: float
    downside: float = 0.0  # non-negative penalty, e.g. expected shortfall max(0,-CVaR)


@dataclass(frozen=True)
class Constraints:
    budget: float
    must_fund: frozenset[str] = frozenset()
    mutually_exclusive: tuple[frozenset[str], ...] = ()
    dependencies: tuple[tuple[str, str], ...] = ()  # (dependent, prerequisite)


@dataclass(frozen=True)
class Portfolio:
    funded: tuple[str, ...]
    cut: tuple[str, ...]
    total_cost: float
    objective: float
    risk_aversion: float
    scores: dict[str, float] = field(default_factory=dict)


_BUDGET_TOL = 1e-9


def _validate(projects: list[Project], c: Constraints) -> None:
    names = [p.name for p in projects]
    if len(names) != len(set(names)):
        raise ValueError("project names must be unique")
    known = set(names)
    referenced = set(c.must_fund)
    for group in c.mutually_exclusive:
        referenced |= set(group)
    for dependent, prerequisite in c.dependencies:
        referenced |= {dependent, prerequisite}
    unknown = referenced - known
    if unknown:
        raise ValueError(f"constraints reference unknown projects: {sorted(unknown)}")


def _is_feasible(selected: frozenset[str], by_name: dict[str, Project], c: Constraints) -> bool:
    if not c.must_fund <= selected:
        return False
    total = sum(by_name[n].cost for n in selected)
    if total > c.budget + _BUDGET_TOL:
        return False
    for group in c.mutually_exclusive:
        if len(selected & group) > 1:
            return False
    for dependent, prerequisite in c.dependencies:
        if dependent in selected and prerequisite not in selected:
            return False
    return True


def optimize(
    projects: list[Project],
    constraints: Constraints,
    risk_aversion: float = 0.0,
) -> Portfolio:
    """Return the feasible portfolio maximizing the risk-adjusted objective.

    Raises ``ValueError`` if no subset satisfies the constraints (e.g. a
    must-fund set that cannot fit the budget).
    """
    _validate(projects, constraints)
    by_name = {p.name: p for p in projects}
    names = list(by_name)
    scores = {
        p.name: p.expected_npv - risk_aversion * p.downside for p in projects
    }

    best: tuple[float, float, frozenset[str]] | None = None
    for size in range(len(names) + 1):
        for combo in combinations(names, size):
            selected = frozenset(combo)
            if not _is_feasible(selected, by_name, constraints):
                continue
            objective = sum(scores[n] for n in selected)
            total_cost = sum(by_name[n].cost for n in selected)
            # Prefer higher objective, then lower cost (deterministic tie-break).
            key = (objective, -total_cost)
            if best is None or key > (best[0], -best[1]):
                best = (objective, total_cost, selected)

    if best is None:
        raise ValueError("no feasible portfolio satisfies the constraints")

    objective, total_cost, selected = best
    funded = tuple(sorted(selected))
    cut = tuple(sorted(set(names) - selected))
    return Portfolio(
        funded=funded,
        cut=cut,
        total_cost=total_cost,
        objective=objective,
        risk_aversion=risk_aversion,
        scores=scores,
    )

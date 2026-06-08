"""Synthetic project corpus — obviously fictional plant capex candidates.

ILLUSTRATIVE / SYNTHETIC. Round, invented numbers; no real company financials,
budgets, or business cases. Authoring believable-but-fictional capital cases is
itself a domain-knowledge artifact (see DECISIONS.md).

The corpus is built to give the optimizer something real to chew on:
  * a **mutually-exclusive pair** — two ways to expand paint capacity (east/west),
  * a **must-fund compliance** project — the emissions scrubber (risk reduction,
    not revenue),
  * a **dependency** — the robot cell needs the power upgrade first,
  * and the **trap** — a flashy specialty-coating line with the highest expected
    NPV but a fat downside tail, because its cost overrun and ramp shortfall are
    *correlated* (they travel together). At high risk-aversion the optimizer cuts
    it; that cut is the whole thesis.

Convention: a project's ``capital`` is the committed, budget-consuming outlay;
the Monte Carlo models the *uncertain* realized outlay and annual cash flows to
get the NPV distribution. All cash flows are level annuities for transparency.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from engine.montecarlo.run import SimulationResult, run_simulation
from engine.montecarlo.sample import Distribution, Triangular
from engine.optimizer.select import Constraints, Project

# --- Demo-wide, documented knobs -------------------------------------------
WACC = 0.10  # single discount rate for the cycle (documented choice for the demo)
SEED = 12345  # fixed so Monte-Carlo demos are reproducible
DEFAULT_N = 20_000  # simulation draws per project
DEMO_BUDGET = 1200.0  # capital cap for the cycle (the UI slider drives this later)

TRAP_NAME = "specialty-coating-line"


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    kind: str
    capital: float
    horizon: int
    inputs: dict[str, Distribution]  # insertion order aligns to ``correlation``
    correlation: np.ndarray
    rationale: str

    def build_cashflows(self, sample: Mapping[str, float]) -> list[float]:
        """Level annuity: uncertain outlay at t0, level annual cash flow after."""
        return [-sample["outlay"]] + [sample["annual"]] * self.horizon


def _independent(k: int) -> np.ndarray:
    return np.eye(k)


def _outlay_annual_corr(rho: float) -> np.ndarray:
    """Correlation between [outlay, annual]. Negative rho = overruns travel with
    ramp shortfalls (high outlay <-> low annual), which fattens the downside tail.
    """
    return np.array([[1.0, rho], [rho, 1.0]])


def corpus() -> list[ProjectSpec]:
    """The 8 synthetic candidates for this capital cycle."""
    return [
        ProjectSpec(
            name="plating-line",
            kind="New plating line",
            capital=500.0,
            horizon=5,
            inputs={
                "outlay": Triangular(450.0, 500.0, 560.0),
                "annual": Triangular(120.0, 160.0, 200.0),
            },
            correlation=_outlay_annual_corr(-0.3),
            rationale="Steady throughput gain; well-understood process.",
        ),
        ProjectSpec(
            name="robot-cell",
            kind="Robotic work cell",
            capital=400.0,
            horizon=5,
            inputs={
                "outlay": Triangular(360.0, 400.0, 470.0),
                "annual": Triangular(100.0, 140.0, 180.0),
            },
            correlation=_outlay_annual_corr(-0.3),
            rationale="Labor savings; requires the power upgrade to run.",
        ),
        ProjectSpec(
            name="power-upgrade",
            kind="Electrical service upgrade",
            capital=100.0,
            horizon=5,
            inputs={
                "outlay": Triangular(90.0, 100.0, 120.0),
                "annual": Triangular(0.0, 15.0, 30.0),
            },
            correlation=_independent(2),
            rationale="Enabling infrastructure; modest direct return.",
        ),
        ProjectSpec(
            name="tank-monitoring",
            kind="Tank-monitoring retrofit",
            capital=150.0,
            horizon=7,
            inputs={
                "outlay": Triangular(140.0, 150.0, 165.0),
                "annual": Triangular(35.0, 45.0, 55.0),
            },
            correlation=_independent(2),
            rationale="Small, steady scrap/quality savings; low risk.",
        ),
        ProjectSpec(
            name="paint-booth-east",
            kind="Paint capacity — east line",
            capital=350.0,
            horizon=6,
            inputs={
                "outlay": Triangular(320.0, 350.0, 400.0),
                "annual": Triangular(70.0, 95.0, 120.0),
            },
            correlation=_outlay_annual_corr(-0.3),
            rationale="One of two ways to add paint capacity (exclusive with west).",
        ),
        ProjectSpec(
            name="paint-booth-west",
            kind="Paint capacity — west line",
            capital=350.0,
            horizon=6,
            inputs={
                "outlay": Triangular(310.0, 350.0, 420.0),
                "annual": Triangular(65.0, 100.0, 130.0),
            },
            correlation=_outlay_annual_corr(-0.3),
            rationale="The other way to add paint capacity (exclusive with east).",
        ),
        ProjectSpec(
            name="emissions-scrubber",
            kind="Emissions scrubber (compliance)",
            capital=200.0,
            horizon=8,
            inputs={
                "outlay": Triangular(180.0, 200.0, 230.0),
                "annual": Triangular(-10.0, 0.0, 15.0),
            },
            correlation=_independent(2),
            rationale="Regulatory must-fund: cost avoidance, not revenue.",
        ),
        ProjectSpec(
            name=TRAP_NAME,
            kind="Specialty-coating line",
            capital=650.0,
            horizon=6,
            # High headline return, but a wide, ugly tail: the realized outlay can
            # blow out AND the annual benefit can collapse, and the two are
            # correlated, so the bad scenario is a *joint* one. The trap.
            inputs={
                "outlay": Triangular(520.0, 650.0, 950.0),
                "annual": Triangular(-80.0, 300.0, 460.0),
            },
            correlation=_outlay_annual_corr(-0.6),
            rationale="Flashy expected NPV; fat downside tail from correlated "
            "overrun + ramp shortfall. The project to defend cutting.",
        ),
    ]


def default_constraints(budget: float = DEMO_BUDGET) -> Constraints:
    """Budget + the corpus's mutually-exclusive / must-fund / dependency rules."""
    return Constraints(
        budget=budget,
        must_fund=frozenset({"emissions-scrubber"}),
        mutually_exclusive=(frozenset({"paint-booth-east", "paint-booth-west"}),),
        dependencies=(("robot-cell", "power-upgrade"),),
    )


@dataclass(frozen=True)
class EvaluatedProject:
    spec: ProjectSpec
    result: SimulationResult  # .npvs (for plots) and .metrics
    candidate: Project  # the optimizer input derived from the metrics


def evaluate(
    spec: ProjectSpec,
    *,
    discount_rate: float = WACC,
    n: int = DEFAULT_N,
    seed: int = SEED,
) -> EvaluatedProject:
    """Monte-Carlo a project into its risk metrics and an optimizer candidate.

    ``downside`` is the expected shortfall as a positive penalty: ``max(0, -CVaR)``.
    """
    result = run_simulation(
        specs=spec.inputs,
        correlation=spec.correlation,
        build_cashflows=spec.build_cashflows,
        discount_rate=discount_rate,
        n=n,
        seed=seed,
    )
    candidate = Project(
        name=spec.name,
        cost=spec.capital,
        expected_npv=result.metrics.mean,
        downside=max(0.0, -result.metrics.cvar),
    )
    return EvaluatedProject(spec=spec, result=result, candidate=candidate)


def evaluate_corpus(
    *,
    discount_rate: float = WACC,
    n: int = DEFAULT_N,
    seed: int = SEED,
) -> list[EvaluatedProject]:
    """Evaluate every project. Each gets a distinct, deterministic seed."""
    return [
        evaluate(spec, discount_rate=discount_rate, n=n, seed=seed + i)
        for i, spec in enumerate(corpus())
    ]


def candidates(evaluated: list[EvaluatedProject]) -> list[Project]:
    """Extract the optimizer inputs from evaluated projects."""
    return [e.candidate for e in evaluated]

"""Orchestration: sample correlated inputs, build cash flows, propagate to NPV.

The caller supplies ``build_cashflows`` mapping one sampled draw (a dict of
named inputs) to a cash-flow vector. M5's project corpus provides these; M2
keeps the engine generic and testable.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from engine.finance.metrics import npv

from .risk import RiskMetrics, summarize
from .sample import Distribution, SampleToCashflows, sample_inputs


@dataclass(frozen=True)
class SimulationResult:
    npvs: np.ndarray
    metrics: RiskMetrics


def run_simulation(
    specs: Mapping[str, Distribution],
    correlation: np.ndarray,
    build_cashflows: SampleToCashflows,
    discount_rate: float,
    n: int,
    seed: int,
    alpha: float = 0.05,
) -> SimulationResult:
    """Run an ``n``-draw correlated Monte Carlo and summarize the NPV distribution.

    Reproducible: the same ``seed`` yields the same draws (and metrics).
    """
    rng = np.random.default_rng(seed)
    samples = sample_inputs(specs, correlation, n=n, rng=rng)
    names = list(samples)
    npvs = np.empty(n, dtype=float)
    for i in range(n):
        draw = {name: float(samples[name][i]) for name in names}
        npvs[i] = npv(discount_rate, build_cashflows(draw))
    return SimulationResult(npvs=npvs, metrics=summarize(npvs, alpha=alpha))

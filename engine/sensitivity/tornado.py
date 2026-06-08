"""Tornado / one-at-a-time sensitivity.

Hold every input at its baseline (mean), swing one input across a percentile
band, and measure how far NPV moves. Ranking the swings answers the honest
question: *which few inputs actually move NPV* — and which ones a CFO should
push back on. Uses the distribution's inverse CDF for band endpoints, so it
works uniformly across normal / triangular / PERT (and never asks an unbounded
normal for its "min").
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from engine.finance.metrics import npv
from engine.montecarlo.sample import Distribution, SampleToCashflows


@dataclass(frozen=True)
class TornadoBar:
    input: str
    low_value: float
    high_value: float
    low_npv: float
    high_npv: float
    base_npv: float

    @property
    def swing(self) -> float:
        """Absolute NPV span across the band — the bar's length."""
        return abs(self.high_npv - self.low_npv)


def tornado(
    specs: Mapping[str, Distribution],
    build_cashflows: SampleToCashflows,
    discount_rate: float,
    band: tuple[float, float] = (0.10, 0.90),
) -> list[TornadoBar]:
    """One ``TornadoBar`` per input, sorted by NPV swing (largest first)."""
    low_q, high_q = band
    baseline = {name: spec.mean for name, spec in specs.items()}
    base_npv = npv(discount_rate, build_cashflows(baseline))

    bars: list[TornadoBar] = []
    for name, spec in specs.items():
        low_value = float(spec.ppf(low_q))
        high_value = float(spec.ppf(high_q))
        low_npv = npv(discount_rate, build_cashflows({**baseline, name: low_value}))
        high_npv = npv(discount_rate, build_cashflows({**baseline, name: high_value}))
        bars.append(
            TornadoBar(
                input=name,
                low_value=low_value,
                high_value=high_value,
                low_npv=low_npv,
                high_npv=high_npv,
                base_npv=base_npv,
            )
        )

    bars.sort(key=lambda bar: bar.swing, reverse=True)
    return bars

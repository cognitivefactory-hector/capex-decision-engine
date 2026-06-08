"""Risk measures over an NPV distribution.

The point estimate is a fiction; these describe the *shape* of the outcome —
especially the downside tail the optimizer (M4) penalizes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def p_loss(npvs: np.ndarray) -> float:
    """P(NPV < 0): the probability the project destroys value."""
    npvs = np.asarray(npvs, dtype=float)
    return float(np.mean(npvs < 0.0))


def cvar(npvs: np.ndarray, alpha: float = 0.05) -> float:
    """Conditional value at risk: the mean of the worst ``alpha`` fraction of
    outcomes (the left tail of NPV). Lower = a fatter, uglier downside.
    """
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    npvs = np.sort(np.asarray(npvs, dtype=float))
    k = max(1, int(np.floor(alpha * npvs.size)))
    return float(npvs[:k].mean())


@dataclass(frozen=True)
class RiskMetrics:
    mean: float
    std: float
    p_loss: float
    cvar: float


def summarize(npvs: np.ndarray, alpha: float = 0.05) -> RiskMetrics:
    """Collapse an NPV sample into the metrics the UI and optimizer consume."""
    npvs = np.asarray(npvs, dtype=float)
    return RiskMetrics(
        mean=float(npvs.mean()),
        std=float(npvs.std()),
        p_loss=p_loss(npvs),
        cvar=cvar(npvs, alpha=alpha),
    )

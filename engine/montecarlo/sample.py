"""Distribution specs and the correlated input sampler.

Correlation is induced with a **Gaussian copula**: draw correlated standard
normals via a Cholesky factor of the correlation matrix, push them through the
normal CDF to uniforms, then map each uniform through its marginal's inverse
CDF. This honors correlation while supporting non-normal marginals (triangular,
PERT) — a cost overrun and a delayed ramp move together, the way real capex does.

Every distribution exposes ``ppf(q)`` (vectorized inverse CDF) and ``mean``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats


class Distribution:
    """Interface: a 1-D marginal with an inverse CDF and a mean."""

    def ppf(self, q: np.ndarray) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError

    mean: float


class Normal(Distribution):
    def __init__(self, mean: float, sd: float):
        self.mean = float(mean)
        self.sd = float(sd)

    def ppf(self, q: np.ndarray) -> np.ndarray:
        return stats.norm.ppf(q, loc=self.mean, scale=self.sd)


@dataclass(frozen=True)
class Triangular(Distribution):
    low: float
    mode: float
    high: float

    def ppf(self, q: np.ndarray) -> np.ndarray:
        width = self.high - self.low
        c = (self.mode - self.low) / width
        return stats.triang.ppf(q, c, loc=self.low, scale=width)

    @property
    def mean(self) -> float:
        return (self.low + self.mode + self.high) / 3.0


@dataclass(frozen=True)
class PERT(Distribution):
    """PERT (a scaled Beta). ``lamb`` weights the mode; 4 is the classic choice."""

    low: float
    mode: float
    high: float
    lamb: float = 4.0

    def ppf(self, q: np.ndarray) -> np.ndarray:
        width = self.high - self.low
        alpha = 1.0 + self.lamb * (self.mode - self.low) / width
        beta = 1.0 + self.lamb * (self.high - self.mode) / width
        return self.low + width * stats.beta.ppf(q, alpha, beta)

    @property
    def mean(self) -> float:
        return (self.low + self.lamb * self.mode + self.high) / (self.lamb + 2.0)


def _cholesky(correlation: np.ndarray) -> np.ndarray:
    corr = np.asarray(correlation, dtype=float)
    if corr.ndim != 2 or corr.shape[0] != corr.shape[1]:
        raise ValueError("correlation must be a square matrix")
    if not np.allclose(corr, corr.T, atol=1e-12):
        raise ValueError("correlation matrix must be symmetric")
    try:
        return np.linalg.cholesky(corr)
    except np.linalg.LinAlgError as exc:
        raise ValueError("correlation matrix must be positive semi-definite") from exc


def sample_inputs(
    specs: Mapping[str, Distribution],
    correlation: np.ndarray,
    n: int,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Draw ``n`` correlated samples for each named input.

    ``correlation`` is aligned to the order of ``specs`` keys (insertion order).
    Returns a dict mapping each name to an array of length ``n``.
    """
    names = list(specs)
    k = len(names)
    correlation = np.asarray(correlation, dtype=float)
    if correlation.shape != (k, k):
        raise ValueError(
            f"correlation must be {k}x{k} to match the {k} inputs; got {correlation.shape}"
        )
    chol = _cholesky(correlation)
    z = rng.standard_normal(size=(n, k))
    correlated = z @ chol.T
    uniforms = stats.norm.cdf(correlated)
    return {
        name: np.asarray(specs[name].ppf(uniforms[:, j]))
        for j, name in enumerate(names)
    }


SampleToCashflows = Callable[[Mapping[str, float]], Sequence[float]]

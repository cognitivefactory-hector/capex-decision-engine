"""Deterministic capital-budgeting metrics.

Convention: ``cashflows[0]`` is the t=0 outlay (negative for an investment) and
``cashflows[i]`` lands at the end of period ``i``. All functions are pure.

IRR is deliberately conservative: when a cash-flow stream has no real internal
rate or more than one (the classic non-conventional-flow trap), :func:`irr`
returns ``None`` rather than an arbitrary pick. :func:`mirr` is the robust
single-valued alternative; :func:`irr_candidates` exposes every real root.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def npv(rate: float, cashflows: Sequence[float]) -> float:
    """Net present value: sum of ``cf_t / (1 + rate)**t``."""
    return float(sum(cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows)))


def irr_candidates(cashflows: Sequence[float], *, tol: float = 1e-9) -> list[float]:
    """Every real internal rate of return (> -100%), ascending.

    Solves ``sum(cf_t * x**t) = 0`` for ``x = 1/(1+r)`` via the polynomial's
    roots, keeps the real positive roots, and maps them back to rates.
    """
    coeffs = np.array(cashflows, dtype=float)
    if coeffs.size < 2 or np.allclose(coeffs, 0.0):
        return []
    # np.roots wants highest-degree coefficient first; our poly is in x = 1/(1+r).
    roots = np.roots(coeffs[::-1])
    rates: list[float] = []
    for x in roots:
        if abs(x.imag) > tol:
            continue
        xr = x.real
        if xr <= tol:  # x > 0 keeps r > -1 (a finite, > -100% rate)
            continue
        rates.append(1.0 / xr - 1.0)
    # De-duplicate numerically-coincident roots.
    rates.sort()
    deduped: list[float] = []
    for r in rates:
        if not deduped or abs(r - deduped[-1]) > 1e-6:
            deduped.append(r)
    return deduped


def irr(cashflows: Sequence[float]) -> float | None:
    """The unique IRR, or ``None`` if there is no real IRR or more than one."""
    cands = irr_candidates(cashflows)
    if len(cands) == 1:
        return cands[0]
    return None


def _periods_to_recover(series: Sequence[float]) -> float | None:
    """Years until the cumulative of ``series`` first reaches zero (interpolated)."""
    cumulative = series[0]
    for i in range(1, len(series)):
        before = cumulative
        cumulative += series[i]
        if cumulative >= 0 and series[i] > 0:
            return (i - 1) + (-before) / series[i]
    return None


def payback(cashflows: Sequence[float]) -> float | None:
    """Undiscounted payback period, or ``None`` if the outlay is never recovered."""
    return _periods_to_recover(list(cashflows))


def discounted_payback(rate: float, cashflows: Sequence[float]) -> float | None:
    """Payback measured on discounted cash flows (>= simple payback)."""
    discounted = [cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows)]
    return _periods_to_recover(discounted)


def profitability_index(rate: float, cashflows: Sequence[float]) -> float:
    """PV of future inflows per dollar of initial outlay (PI > 1 iff NPV > 0)."""
    initial = -cashflows[0]
    if initial <= 0:
        raise ValueError("profitability_index requires a positive initial outlay at t=0")
    pv_future = sum(cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows) if t >= 1)
    return float(pv_future / initial)


def mirr(
    cashflows: Sequence[float],
    *,
    finance_rate: float,
    reinvest_rate: float,
) -> float | None:
    """Modified IRR: positive flows compounded at ``reinvest_rate`` to the horizon,
    negative flows discounted at ``finance_rate`` to t=0.

    Returns ``None`` unless there is at least one inflow and one outflow.
    """
    n = len(cashflows) - 1
    if n < 1:
        return None
    fv_positive = sum(
        cf * (1.0 + reinvest_rate) ** (n - t)
        for t, cf in enumerate(cashflows)
        if cf > 0
    )
    pv_negative = sum(
        cf / (1.0 + finance_rate) ** t for t, cf in enumerate(cashflows) if cf < 0
    )
    if fv_positive <= 0 or pv_negative >= 0:
        return None
    return float((fv_positive / -pv_negative) ** (1.0 / n) - 1.0)

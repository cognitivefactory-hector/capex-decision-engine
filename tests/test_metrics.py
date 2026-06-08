"""M1 — finance core (test-first).

Textbook cash flows with hand-computed expected values. Convention: ``cashflows[0]``
is the t=0 outlay (negative); ``cashflows[i]`` lands at the end of period i.
"""
import math

import pytest

from engine.finance.metrics import (
    discounted_payback,
    irr,
    irr_candidates,
    mirr,
    npv,
    payback,
    profitability_index,
)

# A standard conventional project used across several tests.
CF = [-1000, 500, 400, 300, 100]


# --- NPV -------------------------------------------------------------------

def test_npv_at_zero_rate_is_undiscounted_sum():
    assert npv(0.0, [-100, 50, 50, 50]) == pytest.approx(50.0)


def test_npv_textbook_value():
    # -1000 + 500/1.1 + 400/1.1^2 + 300/1.1^3 + 100/1.1^4
    assert npv(0.10, CF) == pytest.approx(78.81975, abs=1e-4)


def test_npv_single_cashflow_is_itself():
    assert npv(0.25, [-500]) == pytest.approx(-500.0)


# --- IRR -------------------------------------------------------------------

def test_irr_simple_one_period():
    assert irr([-100, 110]) == pytest.approx(0.10)


def test_irr_two_period_compound():
    # (1+r)^2 = 1.21  ->  r = 0.10
    assert irr([-100, 0, 121]) == pytest.approx(0.10)


def test_irr_makes_npv_zero():
    r = irr(CF)
    assert r is not None
    assert npv(r, CF) == pytest.approx(0.0, abs=1e-6)


def test_irr_no_sign_change_returns_none():
    # All inflows: NPV never crosses zero -> no sane IRR.
    assert irr([100, 200, 300]) is None


def test_irr_multiple_roots_returns_none():
    # -100 + 230x - 132x^2 = 0  ->  IRRs at 10% and 20%. Ambiguous -> None.
    assert irr([-100, 230, -132]) is None


def test_irr_candidates_exposes_multiple_roots():
    cands = irr_candidates([-100, 230, -132])
    assert cands == pytest.approx([0.10, 0.20])


# --- Payback ---------------------------------------------------------------

def test_payback_exact_period():
    assert payback([-100, 50, 50, 50]) == pytest.approx(2.0)


def test_payback_fractional_period():
    assert payback([-100, 40, 40, 40]) == pytest.approx(2.5)


def test_payback_never_recovers_returns_none():
    assert payback([-100, 10, 10]) is None


# --- Discounted payback ----------------------------------------------------

def test_discounted_payback_is_at_least_simple_payback():
    cf = [-100, 60, 60]
    assert discounted_payback(0.10, cf) >= payback(cf)


def test_discounted_payback_value():
    # pv: 60/1.1=54.545, 60/1.21=49.587; recovers in 1 + 45.455/49.587 yr
    assert discounted_payback(0.10, [-100, 60, 60]) == pytest.approx(1.91667, abs=1e-4)


# --- Profitability index ---------------------------------------------------

def test_profitability_index_value():
    assert profitability_index(0.10, CF) == pytest.approx(1.07882, abs=1e-4)


def test_pi_greater_than_one_iff_npv_positive():
    assert (profitability_index(0.10, CF) > 1) == (npv(0.10, CF) > 0)


def test_pi_requires_positive_initial_outlay():
    with pytest.raises(ValueError):
        profitability_index(0.10, [0, 100, 100])


# --- MIRR ------------------------------------------------------------------

def test_mirr_textbook_value():
    # FV positives @12%... here finance=reinvest=10%: (1579.5/1000)^(1/4)-1
    assert mirr(CF, finance_rate=0.10, reinvest_rate=0.10) == pytest.approx(
        0.121063, abs=1e-5
    )


def test_mirr_is_defined_when_irr_is_not():
    # The multiple-IRR trap still yields a single, robust MIRR.
    cf = [-100, 230, -132]
    assert irr(cf) is None
    result = mirr(cf, finance_rate=0.10, reinvest_rate=0.10)
    assert result is not None
    assert math.isfinite(result)


def test_mirr_none_without_both_inflow_and_outflow():
    assert mirr([-100, -50], finance_rate=0.10, reinvest_rate=0.10) is None
    assert mirr([100, 50], finance_rate=0.10, reinvest_rate=0.10) is None

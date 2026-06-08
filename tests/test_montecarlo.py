"""M2 — correlated Monte Carlo + risk measures (test-first). The trust core.

Reproducible under a seed; correlation demonstrably honored; CVaR <= mean.
"""
import numpy as np
import pytest

from engine.finance.metrics import npv
from engine.montecarlo.risk import cvar, p_loss, summarize
from engine.montecarlo.run import run_simulation
from engine.montecarlo.sample import (
    PERT,
    Normal,
    Triangular,
    sample_inputs,
)

# --- Marginal distributions ------------------------------------------------

def test_normal_marginal_recovers_mean_and_sd():
    rng = np.random.default_rng(0)
    specs = {"x": Normal(mean=100.0, sd=15.0)}
    out = sample_inputs(specs, np.array([[1.0]]), n=50_000, rng=rng)
    assert out["x"].mean() == pytest.approx(100.0, abs=0.5)
    assert out["x"].std() == pytest.approx(15.0, abs=0.5)


def test_triangular_marginal_mean_and_bounds():
    rng = np.random.default_rng(1)
    specs = {"x": Triangular(low=10.0, mode=20.0, high=60.0)}
    out = sample_inputs(specs, np.array([[1.0]]), n=50_000, rng=rng)
    assert out["x"].mean() == pytest.approx((10.0 + 20.0 + 60.0) / 3, abs=0.5)
    assert out["x"].min() >= 10.0
    assert out["x"].max() <= 60.0


def test_pert_marginal_mean():
    rng = np.random.default_rng(2)
    specs = {"x": PERT(low=10.0, mode=20.0, high=60.0)}
    out = sample_inputs(specs, np.array([[1.0]]), n=50_000, rng=rng)
    # PERT mean = (low + 4*mode + high) / 6
    assert out["x"].mean() == pytest.approx((10.0 + 4 * 20.0 + 60.0) / 6, abs=0.5)


def test_distribution_mean_property():
    assert Normal(mean=5.0, sd=2.0).mean == pytest.approx(5.0)
    assert Triangular(low=0.0, mode=3.0, high=9.0).mean == pytest.approx(4.0)
    assert PERT(low=0.0, mode=3.0, high=9.0).mean == pytest.approx((0 + 12 + 9) / 6)


# --- Correlation (the thing a spreadsheet can't do) ------------------------

def test_positive_correlation_is_honored():
    rng = np.random.default_rng(7)
    specs = {"a": Normal(0.0, 1.0), "b": Normal(0.0, 1.0)}
    corr = np.array([[1.0, 0.8], [0.8, 1.0]])
    out = sample_inputs(specs, corr, n=40_000, rng=rng)
    empirical = np.corrcoef(out["a"], out["b"])[0, 1]
    assert empirical == pytest.approx(0.8, abs=0.03)


def test_independent_inputs_are_uncorrelated():
    rng = np.random.default_rng(8)
    specs = {"a": Normal(0.0, 1.0), "b": Normal(0.0, 1.0)}
    corr = np.eye(2)
    out = sample_inputs(specs, corr, n=40_000, rng=rng)
    empirical = np.corrcoef(out["a"], out["b"])[0, 1]
    assert abs(empirical) < 0.03


def test_non_positive_definite_correlation_raises():
    rng = np.random.default_rng(9)
    specs = {"a": Normal(0.0, 1.0), "b": Normal(0.0, 1.0)}
    bad = np.array([[1.0, 1.5], [1.5, 1.0]])  # |corr| > 1: not valid
    with pytest.raises(ValueError):
        sample_inputs(specs, bad, n=100, rng=rng)


# --- Risk measures ---------------------------------------------------------

def test_p_loss_counts_negative_fraction():
    npvs = np.array([-2.0, -1.0, 1.0, 2.0])
    assert p_loss(npvs) == pytest.approx(0.5)


def test_p_loss_zero_when_all_positive():
    assert p_loss(np.array([1.0, 2.0, 3.0])) == pytest.approx(0.0)


def test_cvar_is_mean_of_worst_tail():
    npvs = np.arange(100.0)  # 0..99
    # worst 5% = lowest 5 values {0,1,2,3,4} -> mean 2.0
    assert cvar(npvs, alpha=0.05) == pytest.approx(2.0)


def test_cvar_not_greater_than_mean():
    rng = np.random.default_rng(11)
    npvs = rng.normal(50.0, 30.0, size=20_000)
    assert cvar(npvs, alpha=0.05) <= npvs.mean()


def test_summarize_reports_all_metrics():
    npvs = np.array([-10.0, 0.0, 10.0, 20.0])
    m = summarize(npvs)
    assert m.mean == pytest.approx(5.0)
    assert m.p_loss == pytest.approx(0.25)
    assert m.cvar <= m.mean


# --- End-to-end simulation -------------------------------------------------

def _project_cashflows(sample):
    # Linear 4-year project: outlay at t0, level annual cash flow after.
    return [-sample["outlay"]] + [sample["annual"]] * 4


def test_run_simulation_is_reproducible_under_seed():
    specs = {"outlay": Normal(1000.0, 50.0), "annual": Normal(300.0, 30.0)}
    corr = np.eye(2)
    kw = dict(
        specs=specs,
        correlation=corr,
        build_cashflows=_project_cashflows,
        discount_rate=0.10,
        n=5_000,
    )
    a = run_simulation(seed=42, **kw)
    b = run_simulation(seed=42, **kw)
    assert np.array_equal(a.npvs, b.npvs)
    assert a.metrics.mean == pytest.approx(b.metrics.mean)


def test_run_simulation_expected_npv_matches_deterministic_at_mean_inputs():
    specs = {"outlay": Normal(1000.0, 50.0), "annual": Normal(300.0, 30.0)}
    corr = np.eye(2)
    result = run_simulation(
        specs=specs,
        correlation=corr,
        build_cashflows=_project_cashflows,
        discount_rate=0.10,
        n=40_000,
        seed=3,
    )
    deterministic = npv(0.10, [-1000.0, 300.0, 300.0, 300.0, 300.0])
    assert result.metrics.mean == pytest.approx(deterministic, abs=1.0)
    assert 0.0 <= result.metrics.p_loss <= 1.0

"""M3 — sensitivity / tornado (test-first).

Vary each input across a percentile band with the others held at baseline,
measure the NPV swing, rank. The "what actually moves NPV" view.
"""
import pytest

from engine.finance.metrics import npv
from engine.montecarlo.sample import Normal, Triangular
from engine.sensitivity.tornado import tornado


def _two_input_linear(sample):
    # Single period at t=1; NPV is linear so swings are hand-checkable.
    return [0.0, 5.0 * sample["a"] + 1.0 * sample["b"]]


def test_returns_one_bar_per_input():
    specs = {"a": Normal(10.0, 2.0), "b": Normal(10.0, 2.0)}
    bars = tornado(specs, _two_input_linear, discount_rate=0.0)
    assert {bar.input for bar in bars} == {"a", "b"}
    assert len(bars) == 2


def test_base_npv_is_npv_at_means():
    specs = {"a": Normal(10.0, 2.0), "b": Normal(10.0, 2.0)}
    bars = tornado(specs, _two_input_linear, discount_rate=0.0)
    expected = npv(0.0, _two_input_linear({"a": 10.0, "b": 10.0}))
    assert bars[0].base_npv == pytest.approx(expected)


def test_larger_coefficient_ranks_first_with_expected_swing():
    specs = {"a": Normal(10.0, 2.0), "b": Normal(10.0, 2.0)}
    bars = tornado(specs, _two_input_linear, discount_rate=0.0, band=(0.10, 0.90))
    # Bars are sorted by swing, descending.
    assert bars[0].input == "a"
    assert bars[1].input == "b"
    # Normal P90-P10 span = 2 * 1.2815515655 * sd = 5.126206 for sd=2.
    assert bars[0].swing == pytest.approx(5.0 * 5.126206, abs=1e-3)
    assert bars[1].swing == pytest.approx(1.0 * 5.126206, abs=1e-3)


def test_wider_range_ranks_first_for_equal_coefficient():
    specs = {
        "wide": Triangular(0.0, 50.0, 100.0),
        "narrow": Triangular(40.0, 50.0, 60.0),
    }

    def build(sample):
        return [0.0, sample["wide"] + sample["narrow"]]

    bars = tornado(specs, build, discount_rate=0.0)
    assert bars[0].input == "wide"
    assert bars[0].swing > bars[1].swing


def test_negative_relationship_is_visible_in_endpoints():
    # Higher outlay -> lower NPV: the high-value endpoint has the lower NPV.
    specs = {"outlay": Normal(1000.0, 50.0)}

    def build(sample):
        return [-sample["outlay"], 300.0, 300.0, 300.0, 300.0]

    (bar,) = tornado(specs, build, discount_rate=0.10)
    assert bar.high_value > bar.low_value
    assert bar.high_npv < bar.low_npv
    assert bar.swing > 0.0

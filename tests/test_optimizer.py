"""M4 — portfolio optimizer (test-first). The decision.

The thesis, encoded: at high risk-aversion the fat-tailed high-NPV "trap" is
cut even though its expected NPV is the highest. Plus the golden invariants:
never over budget, must-fund always funded, mutually-exclusive never both,
dependencies honored.
"""
import pytest

from engine.optimizer.select import Constraints, Project, optimize

# --- The thesis: cutting the high-NPV trap ---------------------------------

def test_lambda_zero_funds_the_highest_expected_npv():
    projects = [
        Project(name="safe", cost=100, expected_npv=50, downside=5),
        Project(name="trap", cost=100, expected_npv=80, downside=200),
    ]
    # Budget fits exactly one project.
    result = optimize(projects, Constraints(budget=100), risk_aversion=0.0)
    assert result.funded == ("trap",)  # pure expected-NPV ranking funds the trap


def test_high_lambda_cuts_the_fat_tailed_trap():
    projects = [
        Project(name="safe", cost=100, expected_npv=50, downside=5),
        Project(name="trap", cost=100, expected_npv=80, downside=200),
    ]
    result = optimize(projects, Constraints(budget=100), risk_aversion=1.0)
    # safe: 50 - 1*5 = 45 ; trap: 80 - 1*200 = -120  -> fund safe, cut the trap.
    assert result.funded == ("safe",)
    assert "trap" in result.cut


# --- Golden invariants -----------------------------------------------------

def test_never_exceeds_budget():
    projects = [
        Project(name="a", cost=60, expected_npv=60),
        Project(name="b", cost=60, expected_npv=55),
        Project(name="c", cost=60, expected_npv=50),
    ]
    result = optimize(projects, Constraints(budget=100), risk_aversion=0.0)
    assert result.total_cost <= 100


def test_exhaustive_picks_the_optimal_knapsack():
    projects = [
        Project(name="p1", cost=60, expected_npv=60),
        Project(name="p2", cost=50, expected_npv=40),
        Project(name="p3", cost=50, expected_npv=45),
    ]
    # Best within 100: {p2, p3} = cost 100, EV 85  (beats {p1} = 60).
    result = optimize(projects, Constraints(budget=100), risk_aversion=0.0)
    assert result.funded == ("p2", "p3")
    assert result.objective == pytest.approx(85.0)


def test_must_fund_is_always_funded_even_if_value_negative():
    projects = [
        Project(name="compliance", cost=50, expected_npv=-10, downside=0),
        Project(name="revenue", cost=50, expected_npv=40, downside=0),
    ]
    result = optimize(
        projects,
        Constraints(budget=100, must_fund=frozenset({"compliance"})),
        risk_aversion=0.0,
    )
    assert "compliance" in result.funded


def test_mutually_exclusive_never_funds_both():
    projects = [
        Project(name="lineA", cost=40, expected_npv=50),
        Project(name="lineB", cost=40, expected_npv=55),
        Project(name="other", cost=40, expected_npv=30),
    ]
    result = optimize(
        projects,
        Constraints(budget=200, mutually_exclusive=(frozenset({"lineA", "lineB"}),)),
        risk_aversion=0.0,
    )
    assert not {"lineA", "lineB"} <= set(result.funded)


def test_dependency_pulls_in_prerequisite():
    projects = [
        Project(name="robot", cost=50, expected_npv=80),
        Project(name="power", cost=30, expected_npv=-5),
    ]
    # robot requires power; robot is attractive enough to drag the prereq in.
    result = optimize(
        projects,
        Constraints(budget=100, dependencies=(("robot", "power"),)),
        risk_aversion=0.0,
    )
    assert "robot" in result.funded
    assert "power" in result.funded


def test_dependency_not_violated_when_dependent_funded():
    projects = [
        Project(name="robot", cost=50, expected_npv=80),
        Project(name="power", cost=30, expected_npv=-5),
    ]
    result = optimize(
        projects,
        Constraints(budget=100, dependencies=(("robot", "power"),)),
        risk_aversion=0.0,
    )
    if "robot" in result.funded:
        assert "power" in result.funded


# --- Result shape and edge cases -------------------------------------------

def test_funded_and_cut_partition_all_projects():
    projects = [
        Project(name="a", cost=40, expected_npv=30),
        Project(name="b", cost=40, expected_npv=20),
    ]
    result = optimize(projects, Constraints(budget=40), risk_aversion=0.0)
    assert set(result.funded) | set(result.cut) == {"a", "b"}
    assert set(result.funded) & set(result.cut) == set()


def test_scores_are_risk_adjusted_values():
    projects = [Project(name="x", cost=10, expected_npv=100, downside=20)]
    result = optimize(projects, Constraints(budget=10), risk_aversion=2.0)
    assert result.scores["x"] == pytest.approx(100 - 2.0 * 20)


def test_infeasible_must_fund_raises():
    projects = [Project(name="big", cost=200, expected_npv=10)]
    with pytest.raises(ValueError):
        optimize(
            projects,
            Constraints(budget=100, must_fund=frozenset({"big"})),
            risk_aversion=0.0,
        )


def test_duplicate_names_raise():
    projects = [
        Project(name="dup", cost=10, expected_npv=10),
        Project(name="dup", cost=20, expected_npv=20),
    ]
    with pytest.raises(ValueError):
        optimize(projects, Constraints(budget=100), risk_aversion=0.0)

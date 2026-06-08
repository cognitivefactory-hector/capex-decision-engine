"""M5 — synthetic project corpus (test-first).

The corpus must load, be obviously synthetic, exercise every constraint type,
and — wired through M2 Monte Carlo into the M4 optimizer — produce an
*interesting* funded-vs-cut split: the trap is funded at low risk-aversion and
cut at high risk-aversion.
"""

from engine.data.projects import (
    DEMO_BUDGET,
    TRAP_NAME,
    candidates,
    corpus,
    default_constraints,
    evaluate_corpus,
)
from engine.optimizer.select import optimize

# Smaller sim count keeps the suite fast; the structure is seed-stable.
TEST_N = 6000


def test_corpus_size_is_five_to_eight():
    specs = corpus()
    assert 5 <= len(specs) <= 8


def test_corpus_names_are_unique():
    names = [s.name for s in corpus()]
    assert len(names) == len(set(names))


def test_constraints_reference_only_real_projects():
    names = {s.name for s in corpus()}
    c = default_constraints(DEMO_BUDGET)
    referenced = set(c.must_fund)
    for group in c.mutually_exclusive:
        referenced |= set(group)
    for dep, prereq in c.dependencies:
        referenced |= {dep, prereq}
    assert referenced <= names


def test_corpus_exercises_every_constraint_type():
    c = default_constraints(DEMO_BUDGET)
    assert c.must_fund  # a compliance must-fund exists
    assert c.mutually_exclusive  # a mutually-exclusive pair exists
    assert c.dependencies  # a dependency exists


def test_trap_has_the_highest_expected_npv():
    evaluated = evaluate_corpus(n=TEST_N)
    by_npv = sorted(evaluated, key=lambda e: e.candidate.expected_npv, reverse=True)
    assert by_npv[0].spec.name == TRAP_NAME


def test_trap_has_the_fattest_downside():
    evaluated = evaluate_corpus(n=TEST_N)
    by_downside = sorted(evaluated, key=lambda e: e.candidate.downside, reverse=True)
    assert by_downside[0].spec.name == TRAP_NAME


def test_evaluation_is_reproducible_under_seed():
    a = {e.spec.name: e.candidate.expected_npv for e in evaluate_corpus(n=TEST_N)}
    b = {e.spec.name: e.candidate.expected_npv for e in evaluate_corpus(n=TEST_N)}
    assert a == b


def test_low_risk_aversion_funds_the_trap():
    cands = candidates(evaluate_corpus(n=TEST_N))
    result = optimize(cands, default_constraints(DEMO_BUDGET), risk_aversion=0.0)
    assert TRAP_NAME in result.funded


def test_high_risk_aversion_cuts_the_trap():
    cands = candidates(evaluate_corpus(n=TEST_N))
    result = optimize(cands, default_constraints(DEMO_BUDGET), risk_aversion=1.0)
    assert TRAP_NAME in result.cut


def test_split_is_interesting_not_all_or_nothing():
    cands = candidates(evaluate_corpus(n=TEST_N))
    result = optimize(cands, default_constraints(DEMO_BUDGET), risk_aversion=1.0)
    assert result.funded  # something funded
    assert result.cut  # something cut


def test_must_fund_and_mutually_exclusive_honored_on_corpus():
    cands = candidates(evaluate_corpus(n=TEST_N))
    c = default_constraints(DEMO_BUDGET)
    result = optimize(cands, c, risk_aversion=0.5)
    assert set(c.must_fund) <= set(result.funded)
    for group in c.mutually_exclusive:
        assert len(set(result.funded) & set(group)) <= 1
    assert result.total_cost <= DEMO_BUDGET

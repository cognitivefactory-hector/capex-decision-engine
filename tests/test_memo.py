"""M6 — investment memo (test-first). The LLM explains; it never decides.

The API is mocked. The contract under test: the prompt is grounded in the
computed numbers (funded/cut, NPVs, CVaR, the cut project), the memo references
the cut high-NPV project, and the model is never asked to choose or recompute.
"""
from types import SimpleNamespace

import pytest

from engine.memo.generate import build_context, generate_memo
from engine.memo.prompts import SYSTEM_PROMPT, build_user_prompt
from engine.memo.schemas import InvestmentMemo
from engine.montecarlo.risk import RiskMetrics
from engine.optimizer.select import Constraints, Portfolio, Project

# --- Fixtures: a funded "safe" project and a cut high-NPV "trap" ------------

def _scenario():
    projects = [
        Project(name="safe-line", cost=100, expected_npv=50.0, downside=5.0),
        Project(name="trap-line", cost=650, expected_npv=281.0, downside=887.0),
        Project(name="scrubber", cost=200, expected_npv=-195.0, downside=250.0),
    ]
    metrics = {
        "safe-line": RiskMetrics(mean=50.0, std=10.0, p_loss=0.10, cvar=-5.0),
        "trap-line": RiskMetrics(mean=281.0, std=400.0, p_loss=0.30, cvar=-887.0),
        "scrubber": RiskMetrics(mean=-195.0, std=20.0, p_loss=1.0, cvar=-250.0),
    }
    kinds = {
        "safe-line": "Steady plating line",
        "trap-line": "Flashy specialty-coating line",
        "scrubber": "Emissions scrubber (compliance)",
    }
    portfolio = Portfolio(
        funded=("safe-line", "scrubber"),
        cut=("trap-line",),
        total_cost=300.0,
        objective=-200.0,
        risk_aversion=1.0,
        scores={"safe-line": 45.0, "trap-line": -606.0, "scrubber": -445.0},
    )
    constraints = Constraints(budget=1200.0, must_fund=frozenset({"scrubber"}))
    return portfolio, projects, metrics, kinds, constraints


def _context():
    portfolio, projects, metrics, kinds, constraints = _scenario()
    return build_context(portfolio, projects, metrics, kinds, constraints)


class _FakeMessages:
    def __init__(self):
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            parsed_output=InvestmentMemo(
                summary="s", funded_rationale="f", cut_rationale="c", risk_note="r"
            )
        )


class _FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()


# --- build_context (pure) --------------------------------------------------

def test_context_partitions_funded_and_cut():
    ctx = _context()
    assert {f.name for f in ctx.funded} == {"safe-line", "scrubber"}
    assert {f.name for f in ctx.cut} == {"trap-line"}


def test_context_surfaces_the_cut_high_npv_project():
    ctx = _context()
    assert ctx.cut_high_npv is not None
    assert ctx.cut_high_npv.name == "trap-line"
    assert ctx.cut_high_npv.expected_npv == pytest.approx(281.0)
    assert ctx.cut_high_npv.cvar == pytest.approx(-887.0)


def test_context_carries_metrics_and_score():
    ctx = _context()
    safe = next(f for f in ctx.funded if f.name == "safe-line")
    assert safe.cvar == pytest.approx(-5.0)
    assert safe.p_loss == pytest.approx(0.10)
    assert safe.score == pytest.approx(45.0)
    assert safe.kind == "Steady plating line"


def test_context_cut_high_npv_is_none_when_nothing_cut():
    portfolio = Portfolio(
        funded=("safe-line",), cut=(), total_cost=100.0, objective=50.0,
        risk_aversion=0.0, scores={"safe-line": 50.0},
    )
    projects = [Project(name="safe-line", cost=100, expected_npv=50.0)]
    metrics = {"safe-line": RiskMetrics(mean=50.0, std=10.0, p_loss=0.1, cvar=-5.0)}
    ctx = build_context(portfolio, projects, metrics, {"safe-line": "Line"},
                        Constraints(budget=200.0))
    assert ctx.cut_high_npv is None


# --- Prompts ---------------------------------------------------------------

def test_system_prompt_forbids_deciding():
    low = SYSTEM_PROMPT.lower()
    assert "optimizer" in low
    assert "already" in low  # the decision is already made
    assert "explain" in low
    # The model must be told not to choose/recompute.
    assert "do not" in low or "must not" in low


def test_user_prompt_is_grounded_in_the_numbers():
    prompt = build_user_prompt(_context())
    assert "trap-line" in prompt  # the cut project is present
    assert "281" in prompt  # its expected NPV
    assert "887" in prompt  # its CVaR
    assert "1200" in prompt  # the budget
    assert "safe-line" in prompt  # a funded project
    assert "CVaR" in prompt


def test_user_prompt_highlights_the_cut_high_npv_project():
    prompt = build_user_prompt(_context())
    # The killed high-NPV project must be explicitly surfaced for the memo.
    assert "trap-line" in prompt
    lowered = prompt.lower()
    assert "cut" in lowered and "highest" in lowered


# --- generate_memo (mocked API) --------------------------------------------

def test_generate_memo_returns_parsed_output():
    client = _FakeClient()
    memo = generate_memo(_context(), client=client)
    assert isinstance(memo, InvestmentMemo)
    assert memo.summary == "s"


def test_generate_memo_passes_computed_numbers_to_the_model():
    client = _FakeClient()
    generate_memo(_context(), client=client)
    (call,) = client.messages.calls
    system_text = " ".join(b["text"] for b in call["system"])
    user_text = " ".join(
        m["content"] if isinstance(m["content"], str) else str(m["content"])
        for m in call["messages"]
    )
    blob = system_text + user_text
    assert "trap-line" in blob  # the cut project
    assert "281" in blob  # its E[NPV]
    assert "887" in blob  # its CVaR
    assert "1200" in blob  # budget


def test_generate_memo_uses_structured_output_schema():
    client = _FakeClient()
    generate_memo(_context(), client=client)
    (call,) = client.messages.calls
    assert call["output_format"] is InvestmentMemo


def test_generate_memo_caches_the_system_prompt():
    client = _FakeClient()
    generate_memo(_context(), client=client)
    (call,) = client.messages.calls
    assert call["system"][0]["cache_control"]["type"] == "ephemeral"


def test_generate_memo_uses_configured_model():
    client = _FakeClient()
    generate_memo(_context(), client=client, model="claude-opus-4-8")
    (call,) = client.messages.calls
    assert call["model"] == "claude-opus-4-8"


def test_generate_memo_defaults_to_sonnet():
    client = _FakeClient()
    generate_memo(_context(), client=client)
    (call,) = client.messages.calls
    assert call["model"] == "claude-sonnet-4-6"

# Decision Record — Capex Decision Engine

The four questions that make judgment portable. These are **first-draft answers** (from `SPEC.md` §1.1) — pressure-test and revise them in the recorded whiteboard session, then keep what survives.

## Situation
A plant always has more capital ideas than budget: a new plating line, a robot cell, a waste-treatment upgrade, a tank-monitoring retrofit. Each arrives with a business case, but they get compared on a **single NPV/IRR point estimate that hides the risk.** Finance and engineering must choose a portfolio under a fixed budget. Facts I have: cost and cash-flow *estimates*. Facts I'm missing: certainty — every input is a range, and a point NPV pretends it isn't.

## Decision
Score each project (NPV/IRR/payback/PI), **Monte-Carlo the uncertain inputs into an NPV distribution**, then **optimize the funded set under the budget cap on a risk-adjusted basis** — and draft an investment memo grounded in those numbers.
**Rejected:** ranking purely by expected NPV (it ignores the downside tail); and letting an LLM "pick the winners" — the optimizer and the numbers decide, the model only *explains.*

## Risk
The killer risk is **over-trusting a point NPV** and funding a project whose downside tail quietly blows the risk budget — capital sunk into a line that underdelivers, a loss nobody attributes to the original decision. Mitigations: expose the full distribution, P(NPV<0), and a CVaR-style downside; **model correlation between inputs** (a cost overrun usually comes with a delayed ramp); choose a portfolio that survives a bad scenario.
**Consciously accepted:** a lower expected return for a tighter downside.

## Change
Capital lands on the risk-adjusted-right projects; and the decision — *including the flashy high-NPV project I cut* — survives a CFO's push-back because the distributions and assumptions are on the table, not buried in a single cell.

## Whiteboard session
- Recording: _TBD_
- The project I killed (and what I funded instead): _…_
- What I revised under push-back / held the line on: _…_

---

## Engineering decisions (recorded as built)
- **Backend:** Django — one stack across the portfolio.
- **Math first, test-first:** finance metrics (incl. multiple-IRR handling → MIRR), correlated Monte Carlo (Cholesky) → P(NPV<0) + CVaR, and a budget-constrained risk-adjusted optimizer. The "cut the high-NPV trap when λ is high" behavior is a passing test — the thesis, encoded.
- **AI:** the LLM never decides — it drafts a memo *grounded in the computed numbers and the optimizer's choice*, which the human edits and signs.
- **Host:** Render (Dockerized) behind Cloudflare. `ANTHROPIC_API_KEY` never committed.

### M0 — scaffold (recorded as built)
- **Framework:** Django 5.x on Python 3.12 (spec requires 3.11+). Chosen over FastAPI to match the portfolio's one-stack rule; server-rendered templates + HTMX (added at M7) keep the front end thin so the substance stays in the quant core.
- **Layout:** three top-level packages — `config/` (Django project), `web/` (thin view layer + templates), and **`engine/`** (the quant core: `finance`, `montecarlo`, `sensitivity`, `optimizer`, `memo`, `data`). `engine/` imports no Django; keeping the math framework-free makes it trivially unit-testable and enforces the "crown jewels are pure" invariant. (This adapts the `app/` layout suggested in `PLAN.md` §"Suggested repo layout".)
- **Memo model:** default **`claude-sonnet-4-6`** (via the `MEMO_MODEL` env var). The memo is one grounded-summarization call per portfolio — Sonnet's quality is ample for prose over already-computed numbers, at materially lower cost/latency than Opus. `claude-opus-4-8` stays available as a quality fallback by overriding the env var. (Revisit at M6 against real memo output.)
- **Optimizer method:** plan to use **exhaustive search with a risk penalty** for the small project count (~5–8), not `scipy.optimize.milp`/`pulp`. With N this small the exhaustive set is tiny and every funded/cut choice is fully explainable — explainability beats cleverness for the whiteboard defense. (Implemented and tested at M4.)
- **Persistence:** SQLite default; no models yet (single-analyst demo). Postgres remains optional later.
- **Dependencies:** single `pyproject.toml` (PEP 621), dev extras (`pytest`, `pytest-django`, `ruff`) under `[project.optional-dependencies]`. Static served by **whitenoise**; container runs **gunicorn**.
- **Acceptance met:** `pytest` green (home page serves 200 + disclaimer present); `ruff` clean; `docker compose up` serves the page under gunicorn.

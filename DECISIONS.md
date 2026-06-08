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

### M1 — finance core (recorded as built)
- **Module:** `engine/finance/metrics.py` — pure functions, built test-first (`tests/test_metrics.py`, 20 cases): `npv`, `irr`, `irr_candidates`, `payback`, `discounted_payback`, `profitability_index`, `mirr`.
- **Convention:** `cashflows[0]` is the t=0 outlay (negative); `cashflows[i]` lands at end of period `i`.
- **IRR edge cases (the known trap).** `irr` is solved as the polynomial roots of `Σ cf_t·x^t = 0` with `x = 1/(1+r)`, keeping real roots with `x > 0` (i.e. rate > −100%). It returns **`None` when there is no real IRR or more than one** (non-conventional flows) rather than picking an arbitrary root. `irr_candidates` exposes every real root so the ambiguity is visible, and **`mirr` is the robust single-valued alternative** (positive flows compounded at the reinvest rate, negatives discounted at the finance rate). This is the "multiple-IRR / no-IRR confusion" mitigation from `PLAN.md`'s risk register — handled in code, surfaced via MIRR.
- **Invariants encoded as tests:** PI > 1 ⟺ NPV > 0; discounted payback ≥ simple payback; IRR makes NPV ≈ 0; MIRR is finite where IRR is undefined.

### M2 — correlated Monte Carlo + risk measures (recorded as built) — the trust core
- **Modules:** `engine/montecarlo/sample.py` (distributions + correlated sampler), `risk.py` (P(NPV<0), CVaR, `summarize`), `run.py` (orchestration). Built test-first (`tests/test_montecarlo.py`, 14 cases).
- **Correlation mechanism: Gaussian copula via Cholesky.** Draw correlated standard normals from `Z @ chol(corr).T`, map through the normal CDF to uniforms, then through each marginal's inverse CDF. Chosen over plain Cholesky-on-covariance because it **honors correlation across non-normal marginals** (triangular/PERT), not just normals — the right tool when a cost overrun and a delayed ramp must move together. Verified: empirical Pearson corr ≈ target within 0.03 at n=40k.
- **Marginals: triangular, PERT, normal.** Triangular/PERT are the intuitive choices for estimate ranges (low/mode/high from domain judgment); normal kept for symmetric inputs. Each exposes a vectorized `ppf` and a `mean` (the latter feeds the "E[NPV] ≈ NPV at mean inputs" sanity check and M3 sensitivity).
- **Downside measure: CVaR (expected shortfall)** at α=5% — the mean of the worst 5% of NPV outcomes — alongside P(NPV<0). CVaR is the tail measure the M4 optimizer penalizes (`expected NPV − λ·downside`); chosen over variance because it speaks to the *bad scenario* directly, which is the whiteboard thesis. Invariant `CVaR ≤ mean` is a test.
- **Reproducibility:** `run_simulation(seed=…)` builds a `numpy.random.default_rng(seed)`; identical seed → identical draws (tested).
- **Generic by design:** the engine takes a `build_cashflows(draw)->cashflows` callback so it stays decoupled from project structure (the M5 corpus supplies specs + cashflow builders per project).

### M3 — sensitivity / tornado (recorded as built)
- **Module:** `engine/sensitivity/tornado.py` — `tornado(specs, build_cashflows, discount_rate, band)` returns one `TornadoBar` per input sorted by NPV swing (largest first). Built test-first (`tests/test_sensitivity.py`, 5 cases).
- **Method: one-at-a-time across a percentile band.** Hold all inputs at baseline (each distribution's `mean`), swing one input to the band endpoints via its **inverse CDF** (`ppf`), recompute NPV. Default band **P10–P90**. Using `ppf` makes the method uniform across normal/triangular/PERT and sidesteps an unbounded normal's nonexistent min/max — cleaner than "low/high" attributes that only some distributions have.
- **`swing = |high_npv − low_npv|`** is the ranking key; endpoints are kept (not just the magnitude) so a *negative* relationship (e.g. higher outlay → lower NPV) stays visible in the chart. This is the "what would change my mind / focus on the few inputs that matter" view from the whiteboard's Q2.

### M4 — portfolio optimizer (recorded as built) — the decision
- **Module:** `engine/optimizer/select.py` — `optimize(projects, constraints, risk_aversion)` → `Portfolio(funded, cut, total_cost, objective, risk_aversion, scores)`. Built test-first (`tests/test_optimizer.py`, 12 cases).
- **Objective:** maximize `Σ_{i∈funded} (expected_npv_i − λ·downside_i)` subject to budget, must-fund, mutually-exclusive (≤1 per group), and dependency (dependent ⇒ prerequisite) constraints. `downside` is a non-negative penalty; the integration layer sets it to the **expected shortfall `max(0, −CVaR)`** from M2.
- **Method: exhaustive enumeration of all subsets**, keeping the feasible one with the best objective (tie-break: lower cost, then deterministic). Chosen over `scipy.optimize.milp`/`pulp` per the M0 decision: for ~5–8 projects it is instant, provably optimal, and — the point — **every funded/cut choice is explainable on a whiteboard**. Explainability beats cleverness here.
- **THE THESIS, ENCODED AS A TEST.** `test_high_lambda_cuts_the_fat_tailed_trap`: with λ=1 the highest-expected-NPV "trap" (EV 80, downside 200) scores −120 and is **cut** in favor of the steadier project (EV 50, downside 5 → 45). At λ=0 the same engine funds the trap. This is the whiteboard's killer Q3, now a passing test.
- **λ (risk_aversion) is the documented, defensible knob** that trades expected return for a tighter downside — the UI budget/λ controls (M7) drive it; the whiteboard defends the chosen value.
- **Honest simplification (defend on camera, whiteboard Q4):** portfolio downside is the **sum of per-project downsides**, not a jointly-simulated portfolio CVaR. This keeps the decision transparent and additive, but it ignores diversification *between* projects (the M2 correlation is *within* a project's inputs, not across projects). A truthful extension is to combine per-project NPV sample arrays and penalize the portfolio's CVaR directly — noted as future work; the per-project form is the explainable MVP.

### M5 — synthetic project corpus (recorded as built)
- **Module:** `engine/data/projects.py` — 8 obviously-fictional plant projects, the demo knobs (`WACC=0.10`, `SEED=12345`, `DEMO_BUDGET=1200`), `evaluate_corpus()` (wires M2 → M4), and `default_constraints()`. Built test-first (`tests/test_corpus.py`, 11 cases). **Synthetic only — round invented numbers, no real financials.** Authoring believable-but-fictional capital cases is itself the domain-knowledge artifact the spec calls for.
- **Discount rate:** a single documented `WACC = 10%` for the cycle (simple, defensible for the demo; tax/depreciation is an explicit non-goal).
- **Cash-flow model:** every project is a level annuity — uncertain `outlay` at t0, level `annual` thereafter over a per-project horizon. Transparent on purpose; the realized outlay (overrun risk) is modeled in the Monte Carlo while the budget consumes the committed `capital`.
- **The corpus exercises all four constraint types:** mutually-exclusive paint-booth pair (east/west), must-fund `emissions-scrubber` (E[NPV] ≈ −195: compliance/cost-avoidance, not revenue), `robot-cell` → `power-upgrade` dependency, and the budget cap.
- **The trap (`specialty-coating-line`), as built:** highest E[NPV] (≈ **281**) of the corpus, but a catastrophic tail — **CVaR ≈ −887** — because its cost overrun and ramp shortfall are **correlated (ρ = −0.6 between outlay and annual)**, so the bad scenario is a *joint* one. This is the M2 correlation feature paying off directly in the thesis (whiteboard Q4).
- **The split, on seeded data (n=20k):** at **λ=0** the optimizer funds the trap (`scrubber + paint-west + trap`, chasing the mean); at **λ≥0.5** it **cuts the trap** for a steadier set (`scrubber + plating + tank + paint-east`). The highest-NPV project is funded only when risk is ignored and cut the moment the tail is priced — the demo's whole point, now reproducible from data.

### M6 — investment memo (recorded as built) — the LLM explains, never decides
- **Modules:** `engine/memo/schemas.py` (`ProjectFact`/`MemoContext` grounding dataclasses + the `InvestmentMemo` Pydantic structured-output schema), `prompts.py` (`SYSTEM_PROMPT` guardrail + `build_user_prompt`), `generate.py` (`build_context` + `generate_memo`). Built test-first (`tests/test_memo.py`, 13 cases, API mocked).
- **The invariant, enforced in code and tests.** The system prompt states the optimizer has *already decided* and the model's only job is to *explain*, grounded strictly in the provided numbers — it must not compute, re-rank, choose, or recommend changes. The grounded user prompt carries the funded/cut lists with their E[NPV], P(NPV<0), CVaR, and risk-adjusted score, the budget/λ, and an explicit callout of the **highest-E[NPV] project that was cut** (the trap) so the memo names it. Tests assert the numbers reach the model, the cut project is surfaced, and the model is never asked to decide.
- **Structured output:** `client.messages.parse(..., output_format=InvestmentMemo)` returns validated sections (`summary`, `funded_rationale`, `cut_rationale`, `risk_note`) — no brittle string parsing.
- **Model & cost:** default `claude-sonnet-4-6` (the M0 decision; overridable, the Django layer passes `settings.MEMO_MODEL`). One call per portfolio, `max_tokens` capped at 2048, **system prompt prompt-cached** (`cache_control: ephemeral`) per the `claude-api` skill's guidance — stable system prompt first, volatile numbers after.
- **Testable & framework-free:** `build_context`/`build_user_prompt` are pure functions; `generate_memo(context, *, client=None)` uses dependency injection so unit tests pass a fake client and never hit the API (one live integration run stays out of CI, per the plan). `engine/` imports no Django.

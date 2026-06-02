# Capex Decision Engine — Implementation Plan

Companion to `SPEC.md`. The build sequence: milestones, concrete tasks, acceptance criteria, and the definition of done. Self-contained — hand this repo to a fresh session and start.

- **Repo:** `capex-decision-engine` (public, under `cognitivefactory-hector`)
- **Approach:** build the **finance math and the optimizer test-first** — they encode the judgment and must be provably correct. The LLM memo is the last, thin layer; it explains, it never decides.

> **Illustrative, not investment advice.** Synthetic projects only. Keep the disclaimer in the footer and README.

---

## The spine (carry through every milestone)

Keep `DECISIONS.md` open and capture reasoning live:

> **Situation** · **Decision** (incl. what you *rejected* — expected-NPV-only ranking; LLM-picks-winners) · **Risk** (incl. what you *accepted* — lower return for a tighter downside) · **Change**.

The hardest decisions (risk-adjusted objective over max-NPV; cutting a high-NPV project) are the spine of the **recorded whiteboard session** — see `SPEC.md` §3.

---

## Prerequisites
- Python 3.11+, Docker, a GitHub account (`gh` authenticated).
- An `ANTHROPIC_API_KEY` (in `.env`, gitignored — **never committed**) for the memo.

---

## Milestones

### M0 — Repo scaffold *(½ day)*
- [ ] Folder + `SPEC.md` + `PLAN.md`.
- [ ] `README.md` (stub + disclaimer), `DECISIONS.md` (paste template from `SPEC.md` §10), `.gitignore` (Python **+ `.env`**), `LICENSE` (MIT).
- [ ] Django (or FastAPI) project; `pyproject.toml`/`requirements.txt`; `Dockerfile`; `docker compose up` serves a page.
- [ ] Record framework + model + optimizer choice in `DECISIONS.md`.
- [ ] `gh repo create … --public --push`.
- **Acceptance:** app serves a page; repo on GitHub; disclaimer present.

### M1 — Finance core (pure, TDD) *(1–2 days)*
**Goal:** provably correct capital-budgeting math.
- [ ] `finance/metrics.py`: NPV, IRR, payback, discounted payback, profitability index, MIRR.
- [ ] Handle IRR edge cases (no real root / multiple roots) gracefully; expose MIRR as the robust alternative.
- [ ] **Tests first:** known textbook cash flows → known NPV/IRR; PI = NPV-per-capital sanity; discounted payback ≥ simple payback.
- **Acceptance:** `pytest` green; IRR edge-case test does not crash and returns a sane signal.

### M2 — Correlated Monte Carlo + risk measures (TDD) *(1–2 days)* — **trust core**
- [ ] `montecarlo/sample.py`: per-input distributions (triangular/PERT/normal) with **correlation** (Cholesky on a covariance matrix).
- [ ] `montecarlo/run.py`: propagate samples → NPV distribution per project; compute mean, **P(NPV<0)**, and **CVaR** (expected shortfall).
- [ ] **Tests:** fixed seed → reproducible stats; positive input correlation produces correlated samples (check empirical corr ≈ target); CVaR ≤ mean.
- **Acceptance:** `pytest` green; correlation is demonstrably honored; reproducible under seed.

### M3 — Sensitivity / tornado *(½ day)*
- [ ] `sensitivity/tornado.py`: vary each input across its range, measure NPV swing, rank.
- [ ] Tests: the input with the widest range / largest coefficient ranks top on a constructed case.
- **Acceptance:** `pytest` green; tornado ordering matches a hand-constructed example.

### M4 — Portfolio optimizer under budget + constraints (TDD) *(1–2 days)* — **the decision**
- [ ] `optimizer/select.py`: choose funded set under a **budget cap** maximizing **expected NPV − λ·downside**, honoring mutually-exclusive, dependency, and must-fund constraints.
- [ ] Method: `scipy.optimize.milp`/`pulp`, or exhaustive-with-risk-penalty for small N (explainable — preferred for the demo).
- [ ] **Tests:** never exceeds budget; respects mutually-exclusive & must-fund; with λ high, the fat-tailed "trap" project is **cut** even though its expected NPV is highest.
- **Acceptance:** `pytest` green; the "cut the high-NPV trap" behavior is a passing test (this *is* the thesis, encoded).

### M5 — Synthetic project corpus *(½ day)*
- [ ] Author 5–8 fictional projects (incl. a mutually-exclusive pair, a must-fund compliance item, and the high-NPV/fat-tail trap), each with uncertainty ranges. (See `SPEC.md` §5.)
- [ ] Fixed seed; obviously synthetic numbers; disclaimer.
- **Acceptance:** corpus loads; the optimizer produces an interesting funded-vs-cut split.

### M6 — Investment memo (LLM, grounded + human-edited) *(1 day)*
- [ ] `memo/generate.py`: Anthropic SDK; **structured output**; pass in the funded list, NPVs, CVaR, constraints, and the cut project; the model **summarizes the optimizer's decision** — it must not compute or choose.
- [ ] Editable memo in the UI; the human signs.
- [ ] Tests (mocked API): the prompt includes the computed numbers; the memo references the cut project; the model is never asked to "decide."
- **Acceptance:** memo reflects the actual funded/cut set; editing works.
- **Note:** if building in Claude Code, invoke the `claude-api` skill here.

### M7 — UI: Projects / Risk / Portfolio tabs *(2 days)*
- [ ] Projects: intake + deterministic metrics table.
- [ ] Risk: NPV distribution plots + tornado per project.
- [ ] Portfolio: **budget slider** → live re-optimize; funded-vs-cut view; "generate memo" button; the **cut high-NPV project** surfaced with its risk reason.
- [ ] Footer disclaimer: "Illustrative capital-budgeting analysis on synthetic projects — not investment advice."
- **Acceptance:** move the budget slider, watch funding change; see distributions (not just points); read a grounded memo.

### M8 — Polish, README, deploy *(1 day)*
- [ ] `README.md`: what/why, one-command run, screenshots/GIF, links to live demo + `DECISIONS.md` + whiteboard video; disclaimers prominent.
- [ ] Deploy with `ANTHROPIC_API_KEY` as a host secret; token cap + caching; smoke-test in prod.
- [ ] Optional: `capex.hector-garza.com`.
- **Acceptance:** public URL works from a fresh browser; full flow runs deployed.

### M9 — Decision Record + Whiteboard session *(½ day)* — **do not skip; this is the differentiator**
- [ ] Complete `DECISIONS.md` (Situation/Decision/Risk/Change; rejected expected-NPV-only; accepted lower-return-for-tighter-downside).
- [ ] Record the 5–8 min whiteboard session using `SPEC.md` §3.1 — center challenge #3 (defending the cut) and #5 (the memo isn't confabulation).
- [ ] Embed/link the recording in README and on hector-garza.com.
- **Acceptance:** a stranger can read `DECISIONS.md` + watch the video and explain *why you cut the highest-NPV project.*

---

## Testing strategy
- **Finance + Monte Carlo + optimizer are the crown jewels — test them hard and first.** Pure, deterministic with seeds.
- Golden invariants: optimizer never exceeds budget; must-fund always funded; mutually-exclusive never both; CVaR ≤ mean; high-λ cuts the fat-tail trap.
- Mock the Anthropic API in unit tests; one live integration run to sanity-check the memo, kept out of CI.
- UI is demonstrated by the recording; don't chase UI coverage.

## Suggested repo layout
```
capex-decision-engine/
├── README.md  SPEC.md  PLAN.md  DECISIONS.md
├── Dockerfile  docker-compose.yml  .env.example  pyproject.toml
├── app/
│   ├── main.py                # Django/FastAPI endpoints
│   ├── finance/  metrics.py
│   ├── montecarlo/ sample.py run.py risk.py
│   ├── sensitivity/ tornado.py
│   ├── optimizer/  select.py
│   ├── memo/       generate.py prompts.py schemas.py
│   ├── data/       projects.py   # synthetic corpus (seeded)
│   └── views.py / templates/ (or web/)
└── tests/ test_metrics.py test_montecarlo.py test_optimizer.py test_memo.py
```

## Risk register (project execution)
| Risk | Mitigation |
|---|---|
| Looks like a spreadsheet — "where's the value?" | Lead with the distribution + the cut; the judgment, not the arithmetic, is the point. |
| Monte Carlo with independent inputs is unrealistic | Model correlation (Cholesky); test it; mention the simplification honestly. |
| LLM appears to "decide" the portfolio | Optimizer decides; memo only explains; enforce in code + tests; say so in README. |
| Multiple-IRR / no-IRR confusion | Handle edge cases; surface MIRR; note it in `DECISIONS.md`. |
| Mistaken for investment advice | Disclaimer in footer + README; non-goals forbid securities advice. |
| Leaking `ANTHROPIC_API_KEY` | `.env` gitignored; host secrets. |
| Skipping M9 because the app "looks done" | M9 *is* the portfolio. The defended cut is the whole point. |

## Definition of Done
See `SPEC.md` §8 — all three deliverables (app, decision record, whiteboard recording) exist and are linked from the README; risk is visible (distributions + downside); the optimizer's budget/constraint honoring is tested; and the "cut the high-NPV trap" behavior is a passing test.

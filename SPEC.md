# Capex Decision Engine — Design Spec

**Project 4 of the Hector Garza portfolio.** Self-contained: everything needed to start this as its own repository is in this file and its companion `PLAN.md`. You do not need any other file from the `career/` folder to build this.

- **Owner:** Hector Garza · hectorg@smartxchain.com · hector-garza.com
- **Status:** Spec — ready to build
- **Suggested repo name:** `capex-decision-engine`
- **One-liner:** A capital-allocation engine that scores plant capex projects on NPV/IRR/payback, Monte-Carlos the uncertain inputs into a *distribution* of outcomes, and picks the risk-adjusted portfolio under a budget cap — built to defend the high-ROI project you deliberately *killed*.

> **Illustrative tool, not investment advice.** Internal capital-budgeting analysis on synthetic projects. No securities recommendations, no real company financials.

---

## 0. Read this first — what this project is *really* for

This is a job-search portfolio project, but it is **not** a "look, it computes NPV" demo. A spreadsheet computes NPV; AI makes building one trivial. The hireable signal is **capital judgment**: choosing what *not* to fund, defending a lower-headline-return choice on risk grounds, and being honest that a point NPV is a fiction.

So this project has **three deliverables of equal weight**:

1. **The working app** (hosted, clickable).
2. **A Decision Record** (`DECISIONS.md`) structured around the four questions below.
3. **A recorded whiteboard session** (5–8 min) where you defend the funded portfolio — and the project you cut — against push-back.

A hiring manager who opens this repo should learn that you allocate capital like someone who's been accountable for the outcome.

---

## 1. The spine — four questions that make judgment portable

Every project in this portfolio is organized around these four questions. They appear here, in `DECISIONS.md`, and on the project's page at hector-garza.com. Fill them in *as you build*, while the reasoning is still alive.

> **1 · Situation** — What's happening, who's involved, the constraints, the facts you have and the facts that are *missing*. Context is where judgment begins.
>
> **2 · Decision** — The plausible paths, the one you took, and the credible options you *rejected*. Rejection shows what you refused to hand-wave.
>
> **3 · Risk** — What could go wrong, what you removed, and what you *consciously accepted*. Prevented losses count — name the bad outcome that didn't happen.
>
> **4 · Change** — What's different now: clearer, safer, faster. Connect the judgment to a real change in the work, not a diary entry.

### 1.1 First-draft answers for Capex Decision Engine (defend/revise these on camera)

These are your starting position. The whiteboard session (§3) exists to pressure-test them — and you've scoped and qualified real process lines, so these are *your* trade-offs.

- **Situation.** A plant always has more capital ideas than budget: a new plating line, a robot cell, a waste-treatment upgrade, a tank-monitoring retrofit. Each arrives with a business case, but they get compared on a **single NPV/IRR point estimate that hides the risk.** Finance and engineering must choose a portfolio under a fixed budget. Facts you have: cost and cash-flow *estimates*. Facts you're missing: certainty — every input is a range, and a point NPV pretends it isn't.
- **Decision.** Build an engine that scores each project (NPV/IRR/payback/PI), **Monte-Carlos the uncertain inputs into an NPV distribution**, then **optimizes the funded set under the budget cap on a risk-adjusted basis** — and drafts an investment memo grounded in those numbers. **You rejected ranking purely by expected NPV** (it ignores the downside tail). **You rejected letting an LLM "pick the winners"** — the optimizer and the numbers decide; the model only *explains.*
- **Risk.** The killer risk is **over-trusting a point NPV** and funding a project whose downside tail quietly blows the risk budget — capital sunk into a line that underdelivers, the loss nobody attributes to the original decision. Mitigations: expose the full distribution, P(NPV<0), and the downside (a CVaR-style tail), **model correlation between inputs** (a cost overrun usually comes with a delayed ramp), and choose a portfolio that survives a bad scenario. You **consciously accept a lower expected return for a tighter downside.**
- **Change.** Capital lands on the risk-adjusted-right projects; and the decision — *including the flashy high-NPV project you cut* — survives a CFO's push-back because the distributions and assumptions are on the table, not buried in a single cell.

---

## 2. Why this project (market fit)

- **AI for capital budgeting is a live category** — ranking projects by NPV/IRR, Monte-Carlo portfolio optimization, and real-time spend monitoring, with reported 10–25% capex savings. FP&A wants a *defensible written rationale*, not just a number.
- It bridges your manufacturing domain and the finance/decision side — useful for industrial-operations, ops-finance, and FP&A-adjacent roles.
- It backs the resume's data/decision narrative and shows you can put a number *and a judgment* on a capital choice.
- **Your unfair advantage:** you've actually scoped, qualified, and lived with new process lines. You know that the cheapest line isn't the best, that ramps slip, and that a waste-treatment upgrade is risk reduction, not revenue. The trade-offs in §1.1 are yours.

---

## 3. The staged whiteboard session (recorded deliverable)

**Format.** 5–8 minutes. Screen + voice (Loom, or OBS → MP4), at the "whiteboard" (a tornado chart / NPV-distribution plot, or the running app), defending the allocation while an adversary pushes back. Use a finance- or ops-literate friend, or answer the scripted challenges below on camera as if presenting to a CFO. Preserve the surviving reasoning in `DECISIONS.md`.

**The point is not the prettiest portfolio.** It's defending a risk-adjusted choice — and a cut — under pressure, conceding fair points without going mushy.

### 3.1 Adversarial challenge script (the push-back)

1. **"NPV ranking is finance 101. Where's the hard part — what did you actually build?"**
   *(Defend the Monte-Carlo over *correlated* inputs, the risk-adjusted portfolio optimization under constraints, and the grounded memo. Distinguish "compute NPV" from "choose a portfolio under uncertainty.")*
2. **"You're just inventing input distributions — garbage in, garbage out. Justify them."**
   *(Defend ranges from domain knowledge, a tornado/sensitivity analysis to show which inputs matter, and honesty that these are estimates to be refined.)*
3. **"You cut the highest-NPV project. A CFO says you left money on the table. Defend it."**
   *(This is the core thesis. Walk the tail: the downside (CVaR), ruin/variance, the risk budget — why expected value isn't the only objective.)*
4. **"Monte Carlo assumes independent inputs. Real capex isn't — overruns and ramp delays travel together. Did you model that?"**
   *(Defend modeled correlation; be honest about what you simplified.)*
5. **"The LLM memo can rationalize any decision. How is it not confabulation?"**
   *(Defend: the memo is generated *from* the computed numbers and the optimizer's choice; the human edits and signs; the model never decides.)*
6. **"Show me the project you killed, and the modest one you funded instead."**
   *(The declined investment — the differentiated artifact.)*

### 3.2 What the recording must show
- The **Situation → Decision → Risk → Change** arc (§1.1), in your words.
- The **cut project** and the risk reasoning behind it.
- At least one place you **revised** under push-back (or a crisp reason you held).
- A pointer to where the surviving reasoning lives (`DECISIONS.md`).

---

## 4. Product specification

### 4.1 Users
- **Primary:** an engineer / ops-finance partner choosing which capital projects to fund this cycle.
- **Demo viewer:** a hiring manager who must "get it" in 60 seconds and see risk-adjusted thinking.

### 4.2 Core features (MVP)
1. **Project intake.** Enter or load candidate projects: name, initial outlay, annual cash flows (or savings) over a horizon, salvage, useful life, and the **uncertainty ranges** per input.
2. **Deterministic metrics.** Per project: NPV (at a stated discount rate / WACC), IRR, payback & discounted payback, profitability index, optional MIRR.
3. **Monte-Carlo simulation.** Sample uncertain inputs (with **correlation** support) → an **NPV distribution** per project: mean, P(NPV<0), and a downside tail (CVaR-style).
4. **Sensitivity / tornado.** Show which inputs move NPV most — the honest "what would change my mind" view.
5. **Portfolio optimizer.** Select the funded set under a **budget cap** to maximize a **risk-adjusted objective** (e.g., expected NPV penalized by downside), honoring constraints: mutually-exclusive projects, dependencies, must-fund (e.g., compliance).
6. **Investment memo (LLM, grounded + human-edited).** Draft a short memo explaining what was funded, what was cut, and *why* — generated from the computed numbers and the optimizer's choice. The engineer edits and signs; the model never decides.
7. **The "killed project" view.** Explicitly surface high-expected-NPV projects that were *not* funded, with the risk reason.

### 4.3 Screens
- **Projects** (intake + deterministic metrics table).
- **Risk** (NPV distributions, tornado/sensitivity per project).
- **Portfolio** (the optimizer result under the budget slider, funded vs. cut, the memo).
- **About / Decision Record** (or link to hector-garza.com): the SDRC story + embedded whiteboard recording.

### 4.4 Explicit non-goals (YAGNI)
- No ERP / accounting / real financial-feed integration; synthetic projects only.
- No securities/investment advice; this is internal capital budgeting.
- The **LLM does not choose** projects — it explains the optimizer's choice. By design.
- No multi-user approvals workflow; a single analyst session is enough.
- No tax/depreciation engine in MVP (note it as a possible extension; keep cash flows simple and stated).

---

## 5. Synthetic data (no employer IP — ever)

Hand-built, obviously fictional candidate projects. **No TAT/MSI numbers, budgets, or business cases.**

- **5–8 sample projects** spanning types you know: new plating line, robot cell, waste-treatment upgrade, tank-monitoring retrofit, paint-booth expansion, etc. — each with round, clearly-synthetic numbers and an uncertainty range per input.
- Include a **mutually-exclusive pair** and a **must-fund compliance** project so the optimizer's constraints have something to chew on.
- Include at least one **"trap": a high-expected-NPV project with a fat downside tail** — the one you'll defend cutting.
- Fixed seed so Monte-Carlo demos are reproducible.

> Authoring believable-but-fictional capital cases is itself a display of your domain expertise — note that in `DECISIONS.md`.

---

## 6. Architecture & stack

Matches the owner's stack (Django · Postgres optional · Docker) with NumPy/SciPy for the math and Claude for the memo.

```
┌──────────────────────────────────────────────────────────┐
│  Browser — Projects / Risk / Portfolio tabs                 │
│   • Plotly: NPV distributions, tornado, funded-vs-cut        │
│   • Budget slider → re-optimize; "generate memo" button      │
└───────────────▲──────────────────────────┬──────────────────┘
                │ JSON                       │
┌───────────────┴──────────────────────────▼──────────────────┐
│  Backend — Django (or FastAPI)                                │
│   • finance/    NPV, IRR, payback, PI, MIRR                   │
│   • montecarlo/ correlated sampling → NPV distribution, CVaR  │
│   • sensitivity/ tornado / one-at-a-time impact               │
│   • optimizer/  budget-constrained risk-adjusted selection    │
│   • memo/       Claude: grounded, human-edited investment memo │
│   • data/       synthetic project corpus (seeded)             │
└───────────────────────────────────────────────────────────────┘
```

**Optimizer:** a 0/1 knapsack / mixed-integer selection under a budget constraint — `scipy.optimize` (`milp`) or `pulp`. For a handful of projects, exhaustive/greedy with a risk penalty is fine and fully explainable (and explainability beats cleverness here).

**Claude integration (decide details at build, then record them):**
- Current frontier model — **`claude-opus-4-8`** or **`claude-sonnet-4-6`** (record cost/quality reasoning).
- **Structured output** for memo sections; **ground every claim in the passed-in numbers** (funded list, NPVs, CVaR, the cut project) — the model summarizes, it does not compute or decide.
- **Prompt caching** for the system prompt + memo template.
- When building the Claude layer, follow Anthropic SDK best practices; in Claude Code, invoke the `claude-api` skill at that point.

**Libraries:** `numpy`, `scipy`, `pandas`, `plotly`, `anthropic`. Lean.

---

## 7. Finance / decision substance (get it right — you'll be asked)

- **NPV** at a stated discount rate (document how you pick WACC for the demo); **IRR** (handle no-real-root / multiple-IRR cases — that's a known trap; mention **MIRR** as the fix); **payback & discounted payback**; **profitability index** (NPV per dollar of capital — useful under a budget constraint).
- **Monte Carlo:** per-input distributions (triangular / PERT / normal as appropriate), **correlation via a covariance/Cholesky or copula approach** so overruns and ramp delays move together; output the NPV distribution, **P(NPV<0)**, and a downside measure (**CVaR / expected shortfall**).
- **Sensitivity / tornado:** vary one input across its range; rank by NPV impact — the "what actually matters" view.
- **Portfolio objective:** not max expected NPV — **max (expected NPV − λ·downside)** under the budget cap, with constraints (mutually exclusive, dependencies, must-fund). The risk-aversion λ is a documented, defensible knob — the whiteboard defends it.
- **The cut:** the engine should be able to fund a lower-expected-NPV project over a higher one when the downside justifies it, and *say so* in the memo.

---

## 8. Definition of Done

Portfolio-ready when **all three** exist and are linked together:

- [ ] **App** deployed at a public URL: load projects → see metrics + NPV distributions + tornado → move the **budget slider** and watch the funded portfolio re-optimize → generate a memo → see the **cut high-NPV project** with its risk reason.
- [ ] **`README.md`** — what/why, one-command local run (Docker), screenshots/GIF, links to live demo + `DECISIONS.md` + whiteboard video, and the illustrative-not-advice + synthetic-data disclaimers.
- [ ] **`DECISIONS.md`** — the §1 four-question template completed, including the rejected expected-NPV-only ranking and the accepted lower-return-for-tighter-downside trade.
- [ ] **Whiteboard recording** (5–8 min) linked from README and embedded on hector-garza.com, including the cut-project defense.
- [ ] **Risk is visible:** the UI shows distributions and the downside, not just point NPVs; the memo is grounded in the numbers and human-edited.
- [ ] Tests pass for the finance functions, correlated Monte-Carlo, and the optimizer's budget/constraint honoring (see `PLAN.md`).

---

## 9. Hosting / deployment
- Containerize (`Dockerfile`); Django/FastAPI runs on Render / Railway / Fly.io / VPS. Postgres optional (a session/in-memory store is fine for the demo).
- Needs an `ANTHROPIC_API_KEY` secret for the memo — **never commit it**; `.env` (gitignored) + host secrets.
- Optional subdomain: `capex.hector-garza.com`; link from the resume's future "Selected Work" section.
- Cost guard: the memo is one call per portfolio; cache and cap tokens.

---

## 10. Repo bootstrap (how to start this as its own repo)

```bash
mkdir capex-decision-engine && cd capex-decision-engine
cp /path/to/04-capex-decision-engine/SPEC.md .
cp /path/to/04-capex-decision-engine/PLAN.md .
# seed: README.md, DECISIONS.md (paste template below), .gitignore (python + .env!), LICENSE (MIT)

git init && git add -A && git commit -m "chore: scaffold capex-decision-engine (spec + plan)"
git branch -M main
gh repo create cognitivefactory-hector/capex-decision-engine --public --source=. --remote=origin --push
```

> PUBLIC repo. **Never commit `ANTHROPIC_API_KEY`** (`.env` gitignored). Synthetic projects only — no real financials.

### `DECISIONS.md` starter (paste into the new repo)

```markdown
# Decision Record — Capex Decision Engine

## Situation
<more ideas than budget; point NPVs hide risk; every input is a range; the future is uncertain>

## Decision
<metrics + correlated Monte Carlo + risk-adjusted optimizer + grounded memo; expected-NPV-only ranking you REJECTED; LLM-picks-winners you REJECTED>

## Risk
<over-trusting point NPV; distribution/CVaR/correlation mitigations; the lower-return-for-tighter-downside trade you ACCEPTED>

## Change
<capital on the risk-adjusted-right projects; the high-NPV project you CUT survives CFO push-back; the prevented sunk loss>

## Whiteboard session
- Recording: <link>
- The project I killed (and what I funded instead): <…>
- What I revised under push-back: <…>
- What I held the line on, and why: <…>
```

---

## 11. Open questions to resolve in the plan
- Optimizer: `scipy.optimize.milp` / `pulp` vs. exhaustive-with-risk-penalty (explainability vs. scale — for ~8 projects, exhaustive is fine and clearer).
- Input distributions: triangular/PERT (intuitive for estimates) vs. normal; and the correlation mechanism (Cholesky vs. copula).
- Risk objective: penalize CVaR vs. variance vs. P(NPV<0) — pick one, defend it.
- Django + templates/HTMX vs. FastAPI + small JS front end.

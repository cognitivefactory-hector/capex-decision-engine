# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

This repo is a **documentation-only scaffold** — there is no application code yet. It currently contains the spec (`SPEC.md`), build plan (`PLAN.md`), decision record (`DECISIONS.md`), and a whiteboard rehearsal (`WHITEBOARD-DRILL.md`). The build follows `PLAN.md` milestones **M0 → M9**; M0 (Django project, `pyproject.toml`/`requirements.txt`, `Dockerfile`, `docker compose`, tooling) has not been done. Until M0 lands, there are no build/test/lint/run commands — establish them per M0 and update this file.

## What this project actually is

A capital-allocation engine that scores synthetic plant capex projects (NPV/IRR/payback/PI/MIRR), Monte-Carlos *correlated* uncertain inputs into an NPV **distribution** per project, then picks a risk-adjusted **portfolio** under a budget cap — and drafts a grounded investment memo.

It is **not** an "it computes NPV" demo. It is a job-search portfolio piece whose hireable signal is *capital judgment*: deliberately **cutting the highest-expected-NPV project** because its downside tail blows the risk budget, and defending that cut. There are **three deliverables of equal weight** (`SPEC.md` §0): the app, `DECISIONS.md`, and a recorded whiteboard session. Do not treat the app as "the deliverable" and the docs as overhead — the defended cut is the whole point (`PLAN.md` risk register: "Skipping M9 because the app looks done").

## Non-negotiable invariants (enforce in code + tests)

These encode the project's thesis. Violating them defeats the project's purpose, not just a style preference:

- **The LLM never decides.** The optimizer and the computed numbers choose the portfolio. The Claude memo only *explains* that choice in prose, grounded in the passed-in figures (funded list, NPVs, CVaR, the cut project), and a human edits/signs. Never let the model rank, pick, or compute. Tests assert the prompt contains the computed numbers and that the model is not asked to decide.
- **Finance math, Monte Carlo, and the optimizer are built test-first.** They are the "crown jewels" — provably correct, pure, deterministic under a fixed seed. The memo is the last, thin layer.
- **The "cut the high-NPV trap" is a passing test.** With risk-aversion λ high, the fat-tailed high-expected-NPV project must be cut. This test *is* the thesis encoded — keep it green.
- **Optimizer golden invariants:** never exceeds budget; must-fund always funded; mutually-exclusive never both funded; dependencies respected.
- **Synthetic data only.** Obviously-fictional projects with round numbers. No real company financials, no employer IP (no TAT/MSI numbers). Fixed seed for reproducible demos.
- **Disclaimer present** in the footer and README: illustrative capital-budgeting analysis on synthetic projects — not investment advice.
- **`ANTHROPIC_API_KEY` is never committed.** `.env` is gitignored; use host secrets in deploy.

## Architecture (planned — see `PLAN.md` "Suggested repo layout")

Django backend with the quant logic split into pure modules under `app/`:
- `finance/` — NPV, IRR (handle no-real-root / multiple-root → expose MIRR), payback & discounted payback, PI, MIRR.
- `montecarlo/` — per-input distributions (triangular/PERT/normal) sampled with **correlation via Cholesky** on a covariance matrix → NPV distribution, P(NPV<0), CVaR.
- `sensitivity/` — tornado: vary each input across its range, rank by NPV swing.
- `optimizer/` — budget-constrained selection maximizing `expected NPV − λ·downside` under constraints. For ~8 projects, exhaustive-with-risk-penalty is preferred over `scipy.optimize.milp`/`pulp` because explainability beats cleverness here.
- `memo/` — Anthropic SDK, structured output, grounded memo (see invariants above).
- `data/` — seeded synthetic project corpus (5–8 projects incl. a mutually-exclusive pair, a must-fund compliance item, and the high-NPV/fat-tail trap).

Frontend: Django templates + HTMX + Plotly. Three tabs — Projects (intake + metrics), Risk (distributions + tornado), Portfolio (budget slider → live re-optimize, funded-vs-cut, generate memo). The cut high-NPV project is surfaced with its risk reason.

Stack: Django · NumPy/SciPy/pandas · Plotly · `anthropic` · Docker · pytest + ruff + GitHub Actions. Deploy target: Dockerized on Render behind Cloudflare (`capex.hector-garza.com`).

## When building the memo layer (M6)

Invoke the `claude-api` skill before writing any Anthropic SDK code. Use a current frontier model (`claude-opus-4-8` or `claude-sonnet-4-6`), structured output for memo sections, and prompt caching for the system prompt + memo template. One call per portfolio; cap tokens. Mock the API in unit tests; keep the one live integration run out of CI.

## Working norms specific to this repo

- **Capture reasoning live in `DECISIONS.md`** as you build — the Situation/Decision/Risk/Change spine and engineering decisions (model choice, optimizer method, correlation mechanism, risk objective). The reasoning is a deliverable, not a postscript.
- Build strictly milestone-by-milestone per `PLAN.md`; each milestone has explicit acceptance criteria.
- Don't chase UI test coverage — the UI is demonstrated by the recording. Spend test effort on finance/Monte-Carlo/optimizer.

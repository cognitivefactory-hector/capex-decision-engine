# Capex Decision Engine

A capital-allocation engine that scores plant capex projects on NPV/IRR/payback, Monte-Carlos the uncertain inputs into a *distribution* of outcomes, and picks the risk-adjusted portfolio under a budget cap — **built to defend the high-ROI project you deliberately *killed*.**

> ⚠️ **Illustrative tool on synthetic projects — not investment advice. No securities recommendations, no real company financials.** This is internal capital-budgeting analysis on hand-built, obviously-fictional projects.

Part of [hector-garza.com](https://hector-garza.com)'s portfolio. One of **three equal deliverables**: the app, a **Decision Record** ([`DECISIONS.md`](./DECISIONS.md)), and a recorded whiteboard session. A working demo no longer proves competence — the judgment behind it does. See [`SPEC.md`](./SPEC.md) §0.

## The point in one sentence

A spreadsheet computes NPV; the hireable signal is **capital judgment** — cutting the highest-expected-NPV project on risk grounds and defending it. This engine makes that decision, shows the distributions behind it, and writes the memo to explain it.

## What it does

- Scores candidate capital projects: **NPV, IRR, payback, profitability index, MIRR** (IRR returns no value when a stream has no single real rate — MIRR is the robust fallback).
- **Monte-Carlos correlated uncertain inputs** → an NPV *distribution* per project: mean, **P(NPV<0)**, and a **CVaR** downside tail. Cost overruns and ramp shortfalls are correlated, so the bad scenario is a joint one.
- **Tornado / sensitivity** — "what would actually change my mind."
- **Risk-adjusted portfolio optimizer** under a budget cap (`max Σ expected NPV − λ·downside`), honoring mutually-exclusive / dependency / must-fund constraints. Move the **budget and λ sliders** and the funded set re-optimizes live.
- A grounded, human-edited **investment memo** — the optimizer decides, the LLM only *explains*, strictly from the computed numbers. It surfaces the high-NPV project that was **cut** with its risk reason.

> **The demo's money shot:** at λ=0 the optimizer funds the flashy `specialty-coating-line` (highest expected NPV); at λ≥0.5 it **cuts it** — its CVaR is catastrophic — for a steadier set. The highest-NPV project is funded only when risk is ignored.

## Screenshots

_Add a short GIF of the Portfolio tab (move the λ slider → the trap gets cut) and a still of the cut-vs-funded distributions here, e.g. `docs/portfolio.gif`._

## Architecture

```
engine/            pure, framework-free, test-first quant core (no Django imports)
├── finance/       NPV, IRR, payback, PI, MIRR
├── montecarlo/    correlated sampling (Gaussian copula) → NPV distribution, P(NPV<0), CVaR
├── sensitivity/   tornado / one-at-a-time impact
├── optimizer/     budget-constrained risk-adjusted selection (exhaustive, explainable)
├── memo/          Claude: grounded, human-edited memo (explains; never decides)
└── data/          synthetic project corpus (seeded, reproducible)

web/               thin Django layer — views + services bridge + templates (HTMX + Plotly)
config/            Django project (settings/urls/wsgi)
```

The math is kept out of Django on purpose: the "crown jewels" (finance, Monte Carlo, optimizer) are pure, deterministic, and unit-tested. The LLM is the last, thin layer and never makes the decision.

## Tech stack

- **Backend:** Django 5 · **Quant:** NumPy / SciPy / pandas · **Charts:** Plotly · **Interactivity:** HTMX
- **AI:** Anthropic SDK (Claude) — structured output, grounded memo, prompt caching, one capped call per portfolio
- **Packaging:** Docker · **Quality:** pytest + ruff + GitHub Actions CI

## Local run

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY to enable the memo (the app serves without it)
docker compose up --build   # → http://localhost:8000
```

Or without Docker:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python manage.py runserver  # → http://localhost:8000
pytest                      # the full test suite
ruff check .                # lint
```

Start on the **Portfolio** tab and move the sliders.

## Deploy

Dockerized Django on **Render**, optionally fronted by **Cloudflare** at `capex.hector-garza.com`.

1. Push to GitHub, then in Render: **New → Blueprint** and point at this repo. [`render.yaml`](./render.yaml) defines the service (Docker, health check at `/healthz/`, generated `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`).
2. Set **`ANTHROPIC_API_KEY`** in the Render dashboard (it's `sync: false` — never committed).
3. For the custom domain, add `capex.hector-garza.com` in Render and point a Cloudflare CNAME at the Render host; it's already in `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS`.

With `DJANGO_DEBUG=False` the app enforces HTTPS redirect, secure cookies, HSTS, and refuses to start on the insecure dev `SECRET_KEY`. Cost guard: the memo is one `max_tokens`-capped call per portfolio with the system prompt cached.

## Links

- 🔗 Live demo: _TBD_
- 🧠 Decision record: [`DECISIONS.md`](./DECISIONS.md) — the four-question judgment narrative
- 📐 Spec & plan: [`SPEC.md`](./SPEC.md) · [`PLAN.md`](./PLAN.md)
- 🎥 Whiteboard walkthrough: _TBD_

## Build

See [`PLAN.md`](./PLAN.md) — M0 (scaffold) → M9. The finance math, correlated Monte Carlo, and the optimizer are built **test-first** (including "cut the high-NPV trap" as a passing test — the thesis, encoded); the memo is the last, thin layer.

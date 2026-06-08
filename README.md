# Capex Decision Engine

A capital-allocation engine that scores plant capex projects on NPV/IRR/payback, Monte-Carlos the uncertain inputs into a *distribution* of outcomes, and picks the risk-adjusted portfolio under a budget cap — built to defend the high-ROI project you deliberately *killed*.

> **Status:** scaffolded (spec + plan in place). Build follows `PLAN.md` (M0 → M9).
> **Illustrative tool on synthetic projects — not investment advice; no securities recommendations.**

Part of [hector-garza.com](https://hector-garza.com)'s portfolio. One of three equal deliverables: the app, a **Decision Record** ([`DECISIONS.md`](./DECISIONS.md)), and a recorded whiteboard session. A working demo no longer proves competence — the judgment behind it does. See [`SPEC.md`](./SPEC.md) §0.

## What it does
- Scores candidate capital projects: NPV, IRR, payback, profitability index, MIRR.
- **Monte-Carlos correlated uncertain inputs** → an NPV distribution per project: mean, P(NPV<0), CVaR downside tail.
- Tornado / sensitivity ("what would change my mind").
- **Risk-adjusted portfolio optimizer** under a budget cap (`max expected NPV − λ·downside`), honoring mutually-exclusive / dependency / must-fund constraints.
- A grounded, human-edited **investment memo** — the optimizer decides, the LLM only explains. Surfaces the high-NPV project that was **cut** with its risk reason.

## Tech stack
- **Backend:** Django
- **Quant:** NumPy / SciPy (Monte Carlo + optimizer); `scipy.optimize.milp` / `pulp` (or exhaustive-with-risk-penalty for small N)
- **AI:** Anthropic SDK (Claude) — structured, grounded memo (does not compute or decide), prompt caching
- **Frontend:** Django templates + HTMX + Plotly
- **Packaging:** Docker · **Quality:** pytest + ruff + GitHub Actions CI

## Deployment
- **Live demo:** Dockerized Django app on **Render**, fronted by **Cloudflare** (planned subdomain `capex.hector-garza.com`).
- `ANTHROPIC_API_KEY` lives in `.env` (gitignored) / host secrets — **never committed.**

### Local run
```bash
cp .env.example .env        # fill in ANTHROPIC_API_KEY for the memo (M6); not needed to serve
docker compose up --build   # → http://localhost:8000
```

Or without Docker:
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python manage.py runserver  # → http://localhost:8000
pytest                      # run the test suite
```

## Links (filled in as the build progresses)
- 🔗 Live demo: _TBD_
- 🧠 Decision record: [`DECISIONS.md`](./DECISIONS.md)
- 🎥 Whiteboard walkthrough: _TBD_

## Build
See [`PLAN.md`](./PLAN.md) — M0 (scaffold) → M9. The finance math, correlated Monte Carlo, and the optimizer are built test-first (incl. "cut the high-NPV trap" as a passing test); the memo is the last, thin layer.

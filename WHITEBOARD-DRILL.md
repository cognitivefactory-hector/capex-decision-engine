# Whiteboard Drill — Capex Decision Engine (design-stage)

> Rehearsal for the recorded whiteboard session. **The push** is me playing tough reviewer; **Defense** is the position that survives; **⚠ Your move** is what only you can answer once you've built/measured it. Fold the survivors into `DECISIONS.md`, then record.
> Scope: design-stage. Re-run after **M4** (optimizer) with the real funded-vs-cut portfolio to defend.

## Q1 — "NPV ranking is finance 101. Where's the hard part — what did you actually build?"
**The push:** This is a spreadsheet.
**Defense (survives):** A spreadsheet ranks point NPVs. I built three things a spreadsheet doesn't: **Monte-Carlo over correlated inputs** → an NPV *distribution* (not a point), a **risk-adjusted portfolio optimizer** under a budget cap with mutually-exclusive/dependency/must-fund constraints, and a memo grounded in those numbers. The decision is "which portfolio under uncertainty," not "compute NPV."
**⚠ Your move:** Point at the optimizer + the distribution as the substance.

## Q2 — "You're inventing input distributions. Garbage in, garbage out."
**The push:** Your ranges are made up.
**Defense (survives):** They're estimates — like every capex case — and I treat them as such: a **tornado/sensitivity analysis** shows which inputs actually move NPV, so the conversation focuses on the few that matter. I'm not claiming precision; I'm making the uncertainty *explicit* instead of hiding it in a single cell.
**⚠ Your move:** From your line-qualification experience, anchor a couple of ranges in something real (typical ramp slippage, overrun %).

## Q3 (the killer) — "You cut the highest-NPV project. A CFO says you left money on the table."
**The push:** Your optimizer is destroying value.
**Defense (survives):** Expected NPV isn't the only objective. That project's **downside tail (CVaR)** blew the risk budget — a fat-tailed bet that, in a bad scenario, sinks capital into an underdelivering line. I funded a modestly-lower-EV project with a tighter downside. I consciously traded a little expected return for survivability, and I can show the distributions that justify it. Optimizing for the mean alone is how you get a portfolio that looks great on paper and occasionally detonates.
**⚠ Your move:** Have the two distributions side by side (the cut vs. the funded) — the picture wins this argument.

## Q4 — "Monte Carlo assumes independent inputs. Real capex isn't — overruns and ramp delays travel together."
**The push:** Your simulation is naive.
**Defense (survives):** Correct, which is why inputs are sampled with **modeled correlation** (Cholesky on a covariance matrix) — a cost overrun is coupled to a delayed ramp, so the tail is fatter and more honest than an independent-sampling toy. I'd rather model the ugly correlation than report a comfortable lie.
**⚠ Your move:** Be ready to name which inputs you correlated and why.

## Q5 — "The LLM memo can rationalize any decision. How is it not confabulation?"
**The push:** The model will justify whatever you tell it.
**Defense (survives):** The memo is generated **from the computed numbers and the optimizer's choice** — funded list, NPVs, CVaR, the cut project — not from free reasoning. The optimizer decides; the LLM only explains the decision in prose, and a human edits and signs. The model never picks winners.
**⚠ Your move:** Show that the prompt is fed the actual figures, and the memo references the real cut.

## Q6 — "Show me the project you killed, and the modest one you funded instead."
**The push:** Where's the judgment?
**Defense (survives):** Here's the high-EV/fat-tail project I cut and the steadier one I funded — defended by the distributions and the risk budget, not vibes. Being able to defend the *uncomfortable* cut is the whole point.
**⚠ Your move:** Build the spec's "trap" project (high expected NPV, fat downside) so the cut is real and on screen.

## Verdict — SDRC after the drill
- **Holds:** risk-adjusted-over-expected-NPV decision; correlation modeling; LLM-explains-not-decides.
- **Sharpen:** lead with **Q3** and the two side-by-side distributions; anchor a range in real experience (Q2); make sure the memo demonstrably consumes the computed numbers (Q5).
- **Land this line in the room:** *"I don't allocate to the highest mean — I allocate to the portfolio that survives a bad year, and I can show you the project I cut to do it."*

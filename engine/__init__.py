"""Framework-free quant core for the Capex Decision Engine.

No Django imports below this package — these are pure, deterministic, unit-tested
modules (the "crown jewels"). The web layer consumes them; the LLM never decides.

Subpackages (built test-first per PLAN.md milestones):
    finance/      M1  NPV, IRR, payback, PI, MIRR
    montecarlo/   M2  correlated sampling -> NPV distribution, P(NPV<0), CVaR
    sensitivity/  M3  tornado / one-at-a-time impact
    optimizer/    M4  budget-constrained risk-adjusted selection
    memo/         M6  Claude: grounded, human-edited investment memo
    data/         M5  synthetic project corpus (seeded)
"""

"""Credit-policy analysis helpers (WoE/IV machinery and hand-tunable binning)."""

from credit_policy.figio import save_fig  # noqa: F401  (re-exported for notebooks)

# Frozen candidate shortlist for Phase 2/3 — single source of truth for notebooks 2.0/2.1/2.2.
# Top-IV slice from 2.1's ranking, minus `regiao` (excluded on fairness / proxy-discrimination
# grounds — see docs/analysis-plan.md). Kept as an explicit list so a re-run with shifted IVs
# cannot silently change membership.
VAR_SELECTION = [
    "classe_social",
    "Capacidade Financeira",
    "score_klavi_2",
    "status_empregaticio",
]

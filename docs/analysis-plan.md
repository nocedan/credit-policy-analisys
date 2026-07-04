# Analysis Plan — Credit Granting Policy Review

**Case**: Fintech client wants to review its credit granting policy using Klavi's variables
(see [case-scenario.md](case-scenario.md)). Deliverable: which variables predict default, which
are practical policy candidates (rules + score), and an objective, justifiable proposal for the
business team — all with a visual, insight-driven approach.

**Working conventions**: cookiecutter-data-science structure; notebooks named
`<phase>.<iteration>-dn-<description>`; raw data never modified in place
(`data/raw` → `data/interim` → `data/processed`); takeaways per notebook in
[reports/key_takeaways.md](../reports/key_takeaways.md).

---

## Phase 0 — Setup

- [x] Conda environment (`credit-policy`: python 3.12, pandas, seaborn, pyarrow, jupyterlab)
- [x] Cookiecutter-style folder structure (without full boilerplate)
- [x] Git repository initialized; data excluded from version control

## Phase 1 — Explore, clean & organize

- [x] **1.0 Initial exploration**: schemas, grain/keys, join coverage, target definition,
      missingness, sentinel values, feature distributions, directional features-vs-target look
- [x] Identify structural issues: many-to-many join, -999999 sentinels, structural missingness,
      target only for `Contratado`, rising vintage default rate
- [x] Draft open questions for the client (target window, Aprovado vs Contratado,
      feature coverage gap, snapshot availability at decision time)
- [ ] **1.1 Cleaning**: sentinels → NaN, dtype fixes (dates, SAFRA), dedup/point-in-time
      snapshot rule (latest `REFERENCIA ≤ DATA`), one-row-per-application modeling table
      written to `data/interim/`
- [ ] Sanity-check the cleaned table: row counts reconcile with raw, no future information
      (leakage check), default rate per safra unchanged by cleaning

## Phase 2 — Feature analysis (relevance & representativeness)

- [ ] **2.0 Univariate signal**: IV / WoE per variable (binned), default rate by decile,
      separation plots (KDE/ROC per variable)
- [ ] Missing-data strategy: treat "no Klavi data" (47.7%) and "no open-finance consent"
      (91.3% for score_klavi_1/Renda/risco_aposta) as explicit segments, not just NaN
- [ ] **Stability**: PSI of each variable across SAFRA; signal stability (IV per vintage)
- [ ] Correlation / redundancy between candidates (e.g. score_klavi_2 × Capacidade Financeira)
- [ ] Leakage screening: any variable suspiciously predictive → challenge its
      point-in-time availability

## Phase 3 — Policy proposal (rules + score)

- [ ] **3.0 Candidate policy design**: simple, explainable rules (cutoffs on
      broad-coverage variables) + score-based ranking for the middle band
- [ ] Swap-set analysis vs. current policy (approve/decline changes and their expected
      default impact)
- [ ] Expected approval rate × default rate trade-off curve to let business choose the
      operating point

## Phase 4 — Validation

- [ ] **What are the key factors or criteria you would consider essential to ensure the insights are relevant, accurate, and representative.**
- [ ] **Out-of-time validation**: train on early safras, validate on the most recent
      mature ones (never random splits only)
- [ ] Discuss selection bias explicitly: performance only observed for `Contratado`;
      bound conclusions accordingly (reject-inference caveats)
- [ ] Robustness: metric confidence intervals (bootstrap), performance by segment
      (region, employment status, feature-coverage segment)
- [ ] Business validation: are the rules actionable, auditable, and compliant with
      how variables are actually available at decision time?

## Phase 5 — Deliverable

- [ ] Executive summary with visuals: what drives default, proposed policy,
      expected impact, caveats and open questions
- [ ] Please detail: the main steps you would take to explore, clean, and organize the provided dataset; key factors or criteria you would consider essential to ensure the insights are relevant, accurate, and representative; how you would validate both the analytical approach and the insights generated;
- [ ] Final recommendation on how to proceed with Klavi's variables
      (which to use now, which need better coverage, what to instrument next)

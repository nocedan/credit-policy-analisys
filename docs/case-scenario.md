# Case Scenario — Credit-Granting Policy Review

**Introduction**:
 You work as a Senior Data Scientist at Klavi, a company specialized in credit risk. A Fintech Client wants to review its credit-granting policy and needs to define:

- Which variables are most relevant for predicting default

- Which variables are good candidates for a practical credit policy (rules + score)

- How to turn these variables into an objective, justifiable proposal for the business team

**Challenge**: You have one week to analyze the data files provided by the client. You must deliver a recommendation on how to proceed using Klavi's variables. With a visual approach, show how to analyze the data and extract meaningful business insights.

**Detail**:

- The main steps you would take to explore, clean, and organize the provided dataset.
- The essential factors or criteria you would consider to ensure the insights are relevant, accurate, and representative.
- How you would validate both the analytical approach and the insights generated.

---

## Answers — variables, policy, and proposal (analysis concluded)

**Why now.** Delinquency (`OVER30M2`) rose from ~8–10% (2024 cohorts) to 12.5%
(Jun/2025) while the approval rate fell from ~54% to ~40%: the bar was tightened and, even so,
default worsened. The current process responds to the scenario by *approving less* -- our proposal would be to *approve better*.

**How to read the numbers.** Everything that is *measured* comes from the labeled sample — the 24,148 `Contracted`
(10.3% default), the only one with observable performance; the
proposal addresses this point head-on (item Q3, "safe expansion").

**Q1 — Which variables are most relevant for predicting default?**
No single variable discriminates strongly — `classe_social` leads, followed closely by `Financial Capacity`, `score_klavi_2` and
`status_empregaticio`. The "open-finance" trio (`score_klavi_1`, `Renda`, `risco_aposta`) is unusable, but because it is **missing in 95.5% of applications**. *Implication:* the policy must
**combine complementary variables**, not rely on a single score. (IV ranking: `classe_social`
0.091 > `Financial Capacity` 0.067 > `score_klavi_2` 0.037 > `status_empregaticio` 0.031 >
`regiao` 0.025.)

**Q2 — Which are good candidates for a practical policy (rules + score)?**
Four variables, all validated (non-redundant, stable over time, no leakage, robust to
re-application): **`classe_social`, `score_klavi_2`, and `status_empregaticio`**.
Two caveats: `regiao`, though relevant (Q1), is **excluded for fairness** — a proxy for
protected attributes; and Financial Capacity, which has negative values -- something to be validated and understood.

**Q3 — How to turn this into an objective, justifiable proposal for the business?**
One possible proposal would be a **two-tier** policy, simple to explain and audit:

1. **Segment** by the stable socioeconomic block — `classe_social` × `status_empregaticio`. It is the
   *stable* part across the observed cohorts.
2. **Cut by score** within each segment (`score_klavi_2`). The score ranks risk end to end
   *within* each cell (in the riskiest D/E, the cut separates 21% from 6% default) — more
   precise and fairer than denying an entire cell.

- **Impact (measured on the book):** at the **same approval level (~90%)**, default drops from **10.3% to
  9.64%**; the rejected slice defaults at 16.3%. The policy corrects distortions of the current bar — today the
  safest cell (`A/B/C·Formal`, 6.5%) is approved *less* than riskier cells.
- **Where Klavi adds value, it refines; where it doesn't, it respects the client's process:** in ~half the funnel
  Klavi receives no snapshot. This does **not** mean a decision without information — granting there follows the
  **client's own process** (its data and score), which Klavi simply does not observe. The proposed bar
  **does not override** that process: it keeps the current decision in that block and concentrates the
  refinement where Klavi actually adds signal.
- **Safe expansion (the selection bias, resolved by design):** performance only exists for the
  contracted, so opening granting to those currently rejected is a *hypothesis*, not a measurement. The recommendation
  **adopts the cuts already in the current flow** (measured effect) and treats expansion as a **staged and
  monitored test** — which, as a bonus, generates the labels that are missing today.

---

## Answers — method (explore, ensure quality, validate)

**1. Explore, clean, and organize.**
I would begin by reconciling the two raw files — `profile_case_credit.parquet` (performance: `uuid`, `DATA`, `SAFRA`,
target `OVER30M2`, `STATUS`) and `transactions_case_credit.parquet` (application features: Klavi scores,
`classe_social`, `status_empregaticio`, `regiao`, income, betting-risk, financial capacity) — into **one row per
application** at the `uuid` + application-date grain, joined on the decision date. The grain is something I would
**validate, not assume**: before settling on it I would test the natural alternative (one application per user per
month) and confirm that same-month re-applications are genuinely distinct events, so the join neither collapses nor
double-counts real decisions. *Tooling:* pandas for the reshape and join; seaborn/matplotlib for the first-pass
distribution and coverage diagnostics that tell me where the data is thin.

Cleaning would be **deliberately conservative** — only provable sentinels (`-999999`) go to `NaN`, and missingness is
carried as an **explicit category** rather than dropped or imputed, because "no snapshot" is itself predictive and
discarding it would bias the sample. I would organize the work in layers (raw → interim → processed) and keep every
judgement call — bin edges, segment definitions, cutoffs — as **version-controlled, human-editable specifications**
driven by reusable functions, so the pipeline is reproducible end to end and any decision can be re-inspected and
revised in one place.

For the variables I would use **Weight-of-Evidence (WoE) binning**: quantile-seeded numeric cut points and one group per
non-rare category, then merged by hand until each variable is **both stable across cohorts and monotone/discriminating**.
I choose WoE because it puts mixed numeric and categorical features on a common, signed risk scale and lets me treat an
explicit `(missing)` bin as a first-class category rather than a gap to impute.

**2. Criteria for relevant, accurate, and representative insight.**
- **Representativeness:** measure only where a target exists (the labeled `Contratado` sample) and state the
  **selection bias** up front — anything estimated on contracted loans is a hypothesis about the rejected population,
  not a measurement of it.
- **Coverage before signal — Information Value on WoE bins:** I would rank variables by **Information Value (IV)**
  computed on the WoE bins (`WoE = ln(%goods/%bads)`, positive = safer, with additive smoothing to stabilize thin
  bins), and **keep the `(missing)` bin inside the IV** so a variable's score reflects how often it is actually
  available, not just how well it separates when present — a strong separator with poor coverage cannot carry a policy.
- **Redundancy — correlation on WoE-encoded, overlap-only rows:** I would WoE-encode the candidates and Pearson-correlate
  them, but only on rows where **both** are observed, to avoid the spurious correlation shared missingness would inject;
  pairs above |r| ≈ 0.5 get pruned or down-weighted so the policy doesn't double-count one underlying signal.
- **Stability over time — PSI + IV per cohort:** only variables that hold cohort by cohort survive. I would track the
  **Population Stability Index (PSI)** of each variable's bin distribution across `SAFRA` (the usual
  < 0.1 / 0.1–0.25 / > 0.25 read) and recompute IV within each cohort, so a one-month artifact can't pass as durable
  signal.
- **Fairness by design:** exclude proxies for protected attributes (e.g. `regiao`) at the design stage, not only after
  checking performance.

**3. Validate approach and insights.**
- **Stability:** confirm the risk ordering is consistent across cohorts, not an artifact of a single month.
- **Two-level policy validation:** where the policy segments and then cuts by score, I would validate each layer
  separately — the **segment baseline** ordering must be sign-consistent cohort by cohort, and the score must order risk
  **monotonically within each segment** before it is trusted as the cutoff axis.
- **Counterfactual impact:** quantify the proposal with a **swap-set analysis** and an **approval × default trade-off
  curve** on the labeled book, so any gain is measured on observed performance rather than promised.
- **Rollout:** apply the cutoffs on the current intake first (observable effect), and expand to the currently-rejected
  population only through a **staged, monitored test** — which also generates the labels that are missing today.

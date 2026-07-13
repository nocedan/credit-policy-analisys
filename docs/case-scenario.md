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
Three variables, all validated (non-redundant, stable over time, no leakage, robust to
re-application): **`classe_social`, `score_klavi_2`, and `status_empregaticio`**.
Two caveats: `regiao`, though relevant (Q1), is **excluded for fairness** — a proxy for
protected attributes; and Financial Capacity, which has negative values -- something to be validated and understood.

**Q3 — How to turn this into an objective, justifiable proposal for the business?**
A **two-tier** policy, simple to explain and audit:

1. **Segment** by the stable socioeconomic block — `classe_social` × `status_empregaticio`. Nearly
   **half the book (49%) carries no Klavi snapshot** (no score, no demographics); this `(missing)`
   block defaults at **11.5%** — below the operating cutoff (τ\* = 11.5%) — so it stays in as a
   **fixed floor**, and the score cut works only on the **~51% of segments Klavi can see**.
2. **Cut by score** (`score_klavi_2`) within each segment. The score orders risk end to end *inside*
   a cell — in the riskiest (D/E) it separates a ~21%-default slice below the cut from ~6% above — so
   a cut is more precise and fairer than denying the whole cell.

- **Impact (one book, re-cut).** At the **same ~90% retention**, the policy lowers default from **10.3%
  to 9.64%** (the 10% it removes default at 16.3%). Both figures come from the *same* 24,148 contracted
  rows scored two ways — keep-all vs. the policy — not two bars applied to different populations. The
  whole gain comes from re-cutting the ~51% named segments (kept at **~7.4%**); the 49% `(missing)` floor
  passes through at 11.5%, which is what holds the blend at 9.64% rather than lower. The policy also fixes
  a distortion of the current bar, which today approves the safest cell (`A/B/C·Formal`, 6.5%) *less* than
  riskier ones.
- **Refine where Klavi has signal, respect the client where it doesn't.** For the ~half of the funnel
  with no snapshot, the policy makes no new call: it keeps the client's own decision (its data, its
  score, which Klavi never sees) and concentrates the refinement where Klavi actually adds signal.
- **Safe expansion (selection bias, handled by design).** Performance exists only for the contracted, so
  lending to today's rejected is a *hypothesis*, not a measurement. The frontier is concentrated: of the
  ~119k rejected applications, the rules would re-admit **~43k (36%)** — almost all in **A/B/C** (no score
  gate, expected ~7.4% vs the 10.3% book), only top-score slivers of **D/E**, and none of `(missing)`. The
  recommendation **adopts the cuts already in the current flow** (a measured effect) and expands only
  through a **staged, monitored test** — which, as a bonus, produces the labels missing today.

---

## Answers — method (explore, ensure quality, validate)

**1. Explore, clean, and organize.**
**Reconciled the two raw files into one row per application** — `profile_case_credit.parquet` (performance) and
`transactions_case_credit.parquet` (features) joined at the `uuid` + application-date grain, on the decision date.
The grain was **validated, not assumed**: the natural alternative (one application per user per month) was tested, and
same-month re-applications turned out to be genuinely distinct contracts (each on its own date), while de-duplicating
would have lost no feature snapshot — so the join neither collapses nor double-counts real decisions.

**Cleaning stayed deliberately conservative** — only provable sentinels (`-999999`) were sent to `NaN`; missingness was
carried as an **explicit category**, never dropped or imputed, because "no snapshot" is itself predictive (~48% of
applications carry none). The work was layered (raw → interim → processed), with every judgement call — bin edges,
segments, cutoffs — kept as an editable spec so any decision can be re-inspected in one place.

**Variables went through Weight-of-Evidence (WoE) binning** — quantile-seeded numeric cuts and one group per non-rare
category, hand-tuned until each was **stable across cohorts and monotone/discriminating**. WoE puts mixed numeric and
categorical features on a common, signed risk scale and makes the `(missing)` bin a first-class category, not a gap to impute.

**2. Criteria for relevant, accurate, and representative insight.**
- **Representativeness — measured only where a target exists** (the labeled `Contratado` sample, 24,148 rows at 10.3%
  bad), with the **selection bias** stated up front: anything estimated on contracted loans is a hypothesis about the
  rejected population, not a measurement.
- **Coverage before signal — IV on WoE bins.** Variables were ranked by **Information Value** (`WoE = ln(%goods/%bads)`,
  positive = safer, 0.5 smoothing on thin bins), keeping the `(missing)` bin **inside** the IV so the score reflects real
  availability — and no variable emerged as a strong separator, which is why the policy combines several rather than leaning on one.
- **Redundancy — WoE correlation, overlap-only.** WoE-encoded candidates were Pearson-correlated on rows where **both**
  are observed; co-missingness otherwise inflates it (`classe_social` × `Financial Capacity` reads 0.73 naively but 0.39
  on the overlap). No pair crossed |r| ≈ 0.5.
- **Stability over time — PSI + IV per cohort.** Each variable's bin distribution was tracked via **PSI** across `SAFRA`
  (< 0.1 / 0.1–0.25 / > 0.25) with IV recomputed within cohorts; three of four held, and `score_klavi_2` — the one
  exception (PSI ≈ 0.32 in one vintage) — was flagged rather than hidden.
- **Fairness by design** — `regiao`, though relevant, was excluded at the design stage as a proxy for protected
  attributes, not after the fact.

**3. Validate approach and insights.**
- **Stability** — the segment risk ordering was confirmed **sign-consistent cohort by cohort**, not an artifact of a single month.
- **Two-level policy validation** — the layers were validated separately: the **segment baseline** ordering first, then
  the score confirmed to **order risk monotonically within each named segment** before it was trusted as the cutoff axis.
- **Counterfactual impact** — the proposal was quantified with a **swap-set analysis** and an **approval × default
  trade-off curve** on the labeled book, so the gain is measured on observed performance, not promised.
- **Rollout** — the cutoffs already present in the current intake were adopted as a measured effect, and expansion to the
  rejected population is staged behind a **monitored test** (which also generates the labels missing today); the
  disparate-impact check on the resulting policy passed.

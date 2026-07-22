# Presentation Outline — Credit-Granting Policy Review

Slide-by-slide structure for the business-team deck, synthesized from the faithful baseline
[`key_takeaways.md`](key_takeaways.md), the concluded answers in
[`docs/case-scenario.md`](../docs/case-scenario.md) §"Answers", and the notebooks (`notebooks/`).

**How to use this file.** One section per slide: **Key message** (the single line the slide must
land), **Bullets** (supporting points, numbers taken verbatim from `key_takeaways.md`), and the
**Figure** (embedded below each slide, with its source notebook). All 9 figures are exported to
`reports/figures/` (saved in-notebook via `credit_policy.save_fig`; re-run the source notebook to
refresh one). Assemble the deck against this outline; keep numbers reconciled with
`key_takeaways.md`.

Storyline: *why now → the data & its catch → Q1 variables → validation → policy & risk tiers →
score axis → trade-off & impact → safe expansion.*

**Naming.** The "open-finance trio" (`score_klavi_1`/`Renda`/`risco_aposta`, ~95.5% missing) is
presented as **The 5% Trio** — a deck-only rename; `key_takeaways.md` and `case-scenario.md`
keep the original "open-finance trio" wording.

---

## Slide 1 — Title

**Key message:** Reviewing the Fintech's credit-granting policy — using Klavi's variables to
improve risk assessment. Analysis of client-provided data.

- Data Scientist; 
- Deliverable: 
    - Which variables predict default?
    - Which are practical policy candidates
    - Example of policy review.
- Author: Daniel Noce da Silva

*Figure: none (title).*

---

## Slide 2 — Why now

**Key message:** The bar was tightened and default *still* rose — the current process responds by
approving less; we propose to improve how risk is assessed.

- Default (`OVER30M2`) climbed from ~**8–10%** (2024 cohorts) to **12.5%** (Jun/2025).
- Approval rate fell from ~**54%** to ~**40%** over the same window.
- The two moved the wrong way together: approvals tightened while default rose.

**Figure** — `fig_deterioration_default_vs_approval.png` · nb 1.0 (dual time series: default rate ↑
vs approval rate ↓ by vintage).

![Default rate rising while approval rate falls, by vintage](figures/fig_deterioration_default_vs_approval.png)

---

## Slide 3 — The data & the catch

**Key message:** Two raw files reconciled to one row per application — and only a labeled
slice has performance (selection bias).

- The target `OVER30M2` exists **only for the 24,148 `Contratado`** applications (**10.30%**
  default).
- A feature snapshot is present at decision time for only **52%** of applications, evenly across
  `STATUS`. Coverage splits in two: broad variables non-missing ~**46%**, The 5% Trio ~**5%**.

**Figure** — `fig_coverage_by_status.png` · nb 1.0 (snapshot coverage by STATUS, showing symmetry;
the labeled 24,148 `Contratado` slice highlighted).

![Snapshot coverage ~52% and uniform across Reprovado/Aprovado/Contratado](figures/fig_coverage_by_status.png)

---

## Slide 4 — Q1: Which variables predict default

**Key message:** No single variable discriminates strongly — the policy must **combine
complementary variables**.

- Ranking: `classe_social` **0.089** >
  `Capacidade Financeira` **0.067** > `score_klavi_2` **0.034** > `status_empregaticio` **0.031** >
  `regiao` **0.025**.
- The 5% Trio (`score_klavi_1`/`Renda`/`risco_aposta`) scores near **0**, driven by
  **95.5%** missingness.

**Figure** — `fig_iv_ranking.png` · nb 2.1 (horizontal IV bar ranking; 0.1 "medium" threshold
marked; The 5% Trio near zero from missingness).

![Information Value per variable, all weak-tier below 0.1](figures/fig_iv_ranking.png)

---

## Slide 5 — Validating the shortlist

**Key message:** All four candidates pass the redundancy, stability, and fairness checks.

- **Redundancy** — every pair correlates below **|r| 0.5** (max **0.39**, `classe_social` ×
  `Capacidade Financeira`) — none redundant enough to drop.
- **Stability** — three are steady across **13** vintages (PSI **0.02–0.03**); `score_klavi_2`
  drifts once (PSI **0.31**), its bins coarsened to 3 monotone.
- **Fairness** — `regiao` carries signal but is excluded as a proxy for protected attributes.

**Figure** — `fig_psi_over_vintage.png` · nb 2.2 (PSI per variable across SAFRA + IV per vintage;
`score_klavi_2` breaches the 0.25 line).

![PSI and IV per vintage; score_klavi_2 the lone unstable variable](figures/fig_psi_over_vintage.png)

---

## Slide 6 — Q3: A two-tier policy

**Key message:** A two-tier policy: segment by the stable socioeconomic block — then score-cut within each named cell.

- **Tier 1 — Segment** by `classe_social` × `status_empregaticio`.
- **Tier 2 — Score cut** on `score_klavi_2` *within* each named cell.
- The named cells fall into three risk tiers: A/B/C **6.5–7.8%** · `(missing)` **11.5%** ·
  D/E **15.5–16.4%** (**2.5×** spread).

**Figure** — `fig_segment_risk_tiers.png` · nb 3.0 (measured default rate by segment vs the
unlabeled stock outside the book).

![Segment default-rate tiers beside the reachable unlabeled stock](figures/fig_segment_risk_tiers.png)

---

## Slide 7 — Score orders risk inside a segment

**Key message:** Every named segment hides a wide risk range — the score is what lets the policy see it.

- `score_klavi_2` orders risk **end-to-end in all 5 named cells**; steepest in
  `D/E · Autônomo/Formal` (**21.4% → 6.1%**, a **3.5×** within-segment spread — wider than the
  **2.5×** spread *between* segments).
- Scoreless applicants inside a named cell default at that cell's own baseline (deltas −2.3 to +1.9 pp).

**Figure** — `fig_score_within_segment.png` · nb 3.1 (default rate by score bin within each named
segment; steepest gradient in `D/E · Autônomo/Formal`).

![Score orders risk within every named segment](figures/fig_score_within_segment.png)

---

## Slide 8 — Trade-off & impact

**Key message:** Default drops **10.30% → 9.64%** without giving up volume — retention stays at
~90%, and τ is applied uniformly across segments.

- **Operating point τ\* = 11.5%** on the named segments, read off the τ-swept approval × default
  frontier *(top figure)*.
- Rules: A/B/C no score gate; D/E score ≥ **595** / ≥ **518**, scoreless denied; `(missing)` keeps the client's own current decision — no Klavi snapshot to score it.
- The removed **10%** defaults at **16.3%** *(bottom figure)*.
- The gain comes from re-cutting the ~**51%** named segments (now ~**7.4%**); the **49%** `(missing)`
  floor passes through unchanged at **11.5%**.

**Figures** — `fig_tradeoff_frontier.png` · nb 3.2 (retention × default frontier, one point per τ;
τ\* = 11.5% and the `(missing)` floor marked) and `fig_swapset_impact.png` · nb 3.2 (keep-all vs
policy v1 on the same 24,148 rows: default 10.30% → 9.64% at ~90% retention).

![Non-monotonic policy frontier with the operating point at tau-star](figures/fig_tradeoff_frontier.png)

![Same book re-cut: default drops from 10.30% to 9.64%](figures/fig_swapset_impact.png)

---

## Slide 9 — Safe expansion under selection bias

**Key message:** Lending to today's rejected is a *hypothesis* — bounded, concentrated, and tested
in stages.

- Of ~**119k** rejected, the rules would re-admit ~**43k** (**36%**): almost all **A/B/C** (no score
  gate, ~**7.4%** expected), only top-score slivers of D/E.
- Any expansion goes through a
  **staged, monitored test**.

**Figure** — `fig_expansion_by_segment.png` · nb 3.2 (re-admittable `Reprovado` volume by segment:
A/B/C concentration, D/E slivers, `(missing)` excluded — 43,093 of 119,247, 36%).

![Re-admittable rejected applications concentrated in A/B/C, none in (missing)](figures/fig_expansion_by_segment.png)

---

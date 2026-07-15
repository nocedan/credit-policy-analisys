---
marp: true
size: 16:9
paginate: true
theme: default
title: Credit-Granting Policy Review
author: Daniel Noce da Silva
---

<style>
:root {
  --brand:#0a5f5f; --brand2:#0d3b3b; --ink:#1b2530; --muted:#5b6b78; --panel:#eef6f6;
}
section {
  font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:20px; color:var(--ink); padding:44px 58px; background:#fff;
  display:flex; flex-direction:column; justify-content:flex-start;
}
h1 { color:var(--brand); font-size:40px; margin:0 0 8px; }
h2 { color:var(--brand); font-size:30px; margin:0 0 12px; }
strong { color:var(--brand); font-weight:700; }
em { color:var(--ink); }
code { background:#eef2f4; padding:1px 5px; border-radius:4px; font-size:.9em; color:#0f3b3b; }
ul { margin:.15em 0; padding-left:1.1em; }
li { margin:.35em 0; line-height:1.38; }
blockquote {
  border-left:4px solid var(--brand); background:var(--panel);
  padding:9px 16px; border-radius:5px; margin:0 0 14px; font-size:20px; color:var(--ink);
}
blockquote p { margin:0; }
.cols { display:grid; grid-template-columns:1.12fr .9fr; gap:26px; align-items:center; margin-top:6px; }
.cols.wide { grid-template-columns:1.3fr .82fr; }
.col img { width:100%; height:auto; border:1px solid #e3e8ea; border-radius:6px; }
.col.figs img { margin-bottom:9px; }
section::after { color:var(--muted); font-size:14px; }
/* dense slides */
section.dense { font-size:18px; }
section.dense li { margin:.28em 0; }
section.dense blockquote { font-size:18px; }
/* title slide */
section.title {
  display:flex; flex-direction:column; justify-content:center; align-items:flex-start;
  background:linear-gradient(135deg,#0a5f5f 0%,#0d3b3b 100%); color:#fff; padding:64px 74px;
}
section.title h1 { color:#fff; font-size:52px; margin-bottom:4px; }
section.title .sub { font-size:27px; color:#d7ecec; margin:8px 0 30px; }
section.title .meta { font-size:19px; color:#bfe0e0; line-height:1.7; }
</style>

<!-- _class: title -->
<!-- _paginate: false -->

# Credit-Granting Policy Review

<div class="sub">Using Klavi's variables to improve risk assessment</div>

<div class="meta">
Daniel Noce da Silva — Senior Data Scientist @ Klavi<br>
One-week analysis of client-provided data<br>
Deliverable: which variables predict default, which are policy candidates, and an objective proposal
</div>

---

## Why now

<div class="cols">
<div class="col">

> The bar was tightened and default *still* rose — the current process responds by approving less; we propose to **improve how risk is assessed**.

- Default (`OVER30M2`) climbed from ~**8–10%** (2024 cohorts) to **12.5%** (Jun/2025).
- Approval rate fell from ~**54%** to ~**40%** over the same window.
- The two moved the wrong way together: approvals tightened while default rose.

</div>
<div class="col">

![](figures/fig_deterioration_default_vs_approval.png)

</div>
</div>

---

## The data & the catch

<div class="cols">
<div class="col">

> Two raw files reconciled to one row per application — and only a labeled slice has performance (**selection bias**).

- The target `OVER30M2` exists **only for the 24,148 `Contratado`** applications (**10.30%** default) — the one slice we can measure.
- A feature snapshot is present at decision time for only **52%** of applications, evenly across `STATUS`. Coverage splits in two: broad variables miss ~**54%**, the open-finance trio ~**95%**.

</div>
<div class="col">

![](figures/fig_coverage_by_status.png)

</div>
</div>

---

## Q1 — Which variables predict default

<div class="cols">
<div class="col">

> No single variable discriminates strongly — the policy must **combine complementary variables**, not lean on one score.

- No variable reaches the **0.1** "medium" IV threshold: `classe_social` **0.089** > `Capacidade Financeira` **0.067** > `score_klavi_2` **0.034** > `status_empregaticio` **0.031** > `regiao` **0.025**.
- The open-finance trio (`score_klavi_1` / `Renda` / `risco_aposta`) scores near **0**, driven by **95.5%** missingness.

</div>
<div class="col">

![](figures/fig_iv_ranking.png)

</div>
</div>

---

<!-- _class: dense -->

## Validating the shortlist

<div class="cols">
<div class="col">

> All four candidates pass the redundancy, stability, leakage, and fairness checks.

- **Redundancy** — every pair correlates below **|r| 0.5** (max **0.39**, `classe_social` × `Capacidade Financeira`), splitting into a socioeconomic block and a financial block. *(A naive **0.73** between those two is a missing-data artifact.)*
- **Stability** — three are steady across **13** vintages (PSI **0.02–0.03**); `score_klavi_2` drifts once (PSI **0.31**), its bins coarsened to 3 monotone.
- **Leakage** — none; every candidate is a weak, point-in-time signal.
- **Fairness** — `regiao` carries signal but is excluded as a proxy for protected attributes.

</div>
<div class="col">

![](figures/fig_psi_over_vintage.png)

</div>
</div>

---

<!-- _class: dense -->

## Q3 — A two-tier policy

<div class="cols">
<div class="col">

> Segment by the stable socioeconomic block — which orders cleanly into three risk tiers (**2.4×** spread) — then score-cut within each named cell.

- **Tier 1 — Segment** by `classe_social` × `status_empregaticio`: **5** named cells + `(missing)`.
- **Tier 2 — Score cut** on `score_klavi_2` *within* each named cell.
- The named cells fall into three risk tiers: A/B/C **6.5–7.8%** · `(missing)` **11.5%** · D/E **15.5–16.4%** (**2.4×** spread).
- `(missing)` is **49%** of the book and carries no snapshot, so it sits at a fixed **11.5%** floor; the score cut reaches only the ~**51%** Klavi can see.
- Today's bar misorders risk: `A/B/C · Formal` (safest, **6.5%**) is approved **43.7%** — less than a riskier A/B/C cell at **50.1%** (**7.8%**).

</div>
<div class="col">

![](figures/fig_segment_risk_tiers.png)

</div>
</div>

---

## Score orders risk inside a segment

<div class="cols">
<div class="col">

> A score cut is more precise *and* fairer than denying a whole cell.

- `score_klavi_2` orders risk **end-to-end in all 5 named cells**; steepest in `D/E · Autônomo/Formal` (**21.4% → 6.1%**).
- Scoreless applicants inside a named cell default at that cell's own baseline.

</div>
<div class="col">

![](figures/fig_score_within_segment.png)

</div>
</div>

---

<!-- _class: dense -->

## Trade-off & impact

<div class="cols">
<div class="col">

> At the same ~**90%** retention, default drops **10.30% → 9.64%** — measured on the same book using the same risk-tolerance **τ** per segment.

- **Operating point τ\* = 11.5%** on the named segments, read off the τ-swept approval × default frontier *(left)*.
- Rules: A/B/C no score gate; D/E score ≥ **595** / ≥ **518**, scoreless denied; `(missing)` deferred.
- The removed **10%** defaults at **16.3%** *(right)*.
- The gain comes from re-cutting the ~**51%** named segments (now ~**7.4%**); the **49%** `(missing)` floor passes through unchanged at **11.5%**.

</div>
<div class="col figs">

![](figures/fig_tradeoff_frontier.png)

![](figures/fig_swapset_impact.png)

</div>
</div>

---

<!-- _class: dense -->

## Safe expansion under selection bias

<div class="cols">
<div class="col">

> Lending to today's rejected is a *hypothesis* — bounded, concentrated, and tested in stages.

- Of ~**119k** rejected, the rules would re-admit ~**43k** (**36%**): almost all **A/B/C** (no score gate, ~**7.4%** expected), only top-score slivers of D/E, and none of `(missing)`.
- The `(missing)` block stays with the client's own decision, since Klavi has no snapshot there.
- The cuts already run in current intake (a measured effect); any expansion goes through a **staged, monitored test** that also generates today's missing labels.

</div>
<div class="col">

![](figures/fig_expansion_by_segment.png)

</div>
</div>

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
  --brand:#123a5e; --brand2:#0d2740; --ink:#16202b; --muted:#51606e; --panel:#eef2f7;
  --risk-low:#0d9488; --risk-mid:#d98a00; --risk-high:#d03b3b;
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
.wfig img { display:block; margin:8px auto 0; width:auto; max-width:100%; height:auto;
            border:1px solid #e3e8ea; border-radius:6px; }
/* px, not vh: in the HTML export vh resolves against the browser window, not the
   720px slide, which blows the figure past the slide bounds. The slide is a fixed
   1280x720, so px caps are stable in both HTML and PDF. */
.wfig.big img { max-height:316px; }
.wfig.mid img { max-height:266px; }
.wfig.sm  img { max-height:216px; }
section::after { color:var(--muted); font-size:14px; }
/* dense slides */
section.dense { font-size:18px; }
section.dense li { margin:.28em 0; }
section.dense blockquote { font-size:18px; }
/* title slide */
section.title {
  display:flex; flex-direction:column; justify-content:center; align-items:flex-start;
  background:linear-gradient(135deg,#123a5e 0%,#0d2740 100%); color:#fff; padding:64px 74px;
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
Daniel Noce da Silva — Data Scientist<br>
Analysis of client-provided data<br>
Deliverable: which variables predict default, which are policy candidates, and an example of policy review
</div>

---

## Why now

> The bar was tightened and default *still* rose — the current process responds by approving less; we propose to **improve how risk is assessed**.

- Default (`OVER30M2`) climbed from ~**8–10%** (2024 cohorts) to **12.5%** (Jun/2025).
- Approval rate fell from ~**54%** to ~**40%** over the same window.
- The two moved the wrong way together: approvals tightened while default rose.

<div class="wfig big">

![](figures/fig_deterioration_default_vs_approval.png)

</div>

---

## The data & the catch

> Two raw files reconciled to one row per application — and only a labeled slice has performance (**selection bias**).

- The target `OVER30M2` exists **only for the 24,148 `Contratado`** applications (**10.30%** default).
- A feature snapshot is present at decision time for only **52%** of applications, evenly across `STATUS`. Coverage splits in two: broad variables non-missing ~**46%**, the open-finance trio ~**5%**.

<div class="wfig big">

![](figures/fig_coverage_by_status.png)

</div>

---

## Q1 — Which variables predict default

> No single variable discriminates strongly — the policy must **combine complementary variables**.

- One variable is close to the **0.1** "medium" IV threshold. Ranking: `classe_social` **0.089** > `Capacidade Financeira` **0.067** > `score_klavi_2` **0.034** > `status_empregaticio` **0.031** > `regiao` **0.025**.
- The open-finance trio (`score_klavi_1` / `Renda` / `risco_aposta`) scores near **0**, driven by **95.5%** missingness.

<div class="wfig big">

![](figures/fig_iv_ranking.png)

</div>

---

<!-- _class: dense -->

## Validating the shortlist

> All four candidates pass the redundancy, stability, and fairness checks.

- **Redundancy** — every pair correlates below **|r| 0.5** (max **0.39**, `classe_social` × `Capacidade Financeira`) — none redundant enough to drop. *(A naive **0.73** between those two is a missing-data artifact.)*
- **Stability** — three are steady across **13** vintages (PSI **0.02–0.03**); `score_klavi_2` drifts once (PSI **0.31**), its bins coarsened to 3 monotone.
- **Fairness** — `regiao` carries signal but is excluded as a proxy for protected attributes.

<div class="wfig big">

![](figures/fig_psi_over_vintage.png)

</div>

---

<!-- _class: dense -->

## Q3 — A two-tier policy

> Segment by the stable socioeconomic block — which orders cleanly into three risk tiers (**2.5×** spread) — then score-cut within each named cell.

- **Tier 1 — Segment** by `classe_social` × `status_empregaticio`: **5** named cells + `(missing)`.
- **Tier 2 — Score cut** on `score_klavi_2` *within* each named cell.
- The named cells fall into three risk tiers: A/B/C **6.5–7.8%** · `(missing)` **11.5%** · D/E **15.5–16.4%** (**2.5×** spread).
- `(missing)` is **49%** of the book and carries no snapshot, so it sits at a fixed **11.5%** floor; the score cut reaches only the ~**51%** Klavi can see.
- Today's bar misorders risk: `A/B/C · Formal` (safest, **6.5%**) is approved **43.7%** — less than a riskier A/B/C cell at **50.1%** (**7.8%**). *(`D/E · Formal`, 22 labeled, merged into `D/E · Autônomo/Formal`.)*

<div class="wfig sm">

![](figures/fig_segment_risk_tiers.png)

</div>

---

## Score orders risk inside a segment

> Every named segment hides a wide risk range — the score is what lets the policy see it.

- `score_klavi_2` orders risk **end-to-end in all 5 named cells**; steepest in `D/E · Autônomo/Formal` (**21.4% → 6.1%**, a **3.5×** within-segment spread — wider than the **2.5×** spread *between* segments).
- Scoreless applicants inside a named cell default at that cell's own baseline (deltas −2.3 to +1.9 pp).

<div class="wfig big">

![](figures/fig_score_within_segment.png)

</div>

---

<!-- _class: dense -->

## Trade-off & impact

<div class="cols">
<div class="col">

> Default drops **10.30% → 9.64%** without giving up volume — retention stays at ~**90%**, and **τ** is applied uniformly across segments.

- **Operating point τ\* = 11.5%** on the named segments, read off the τ-swept approval × default frontier *(top)*.
- Rules: A/B/C no score gate; D/E score ≥ **595** / ≥ **518**, scoreless denied; `(missing)` keeps the client's own current decision — no Klavi snapshot to score it.
- The removed **10%** defaults at **16.3%** *(bottom)*.
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

> Lending to today's rejected is a *hypothesis* — bounded, concentrated, and tested in stages.

- Of ~**119k** rejected, the rules would re-admit ~**43k** (**36%**): almost all **A/B/C** (no score gate, ~**7.4%** expected), only top-score slivers of D/E.
- Any expansion goes through a **staged, monitored test**.

<div class="wfig mid">

![](figures/fig_expansion_by_segment.png)

</div>

# Are WoE bins real? Significance & stability testing

A methodology reference for two questions that recur whenever a WoE-binned variable looks
shaky across cohorts (motivating case: `score_klavi_2`, whose per-`SAFRA` WoE lines cross in
7 of 13 cohorts — see notebook 2.0 §6 and the stability screen in 2.2 §3):

1. **Are the bins genuinely different**, or are the WoE gaps within sampling noise?
2. **Are the cohort-to-cohort inversions real instability**, or a low-volume artifact?

Both are answered with standard categorical-data inference once you use the right unit of
analysis. Companion to `references/information-value.md` (WoE/IV) and
`references/population-stability.md` (PSI). Everything below is on the labeled `Contratado`
sample; "bad" = `OVER30M2 = 1`.

## The key identity: a WoE difference is a log odds-ratio

Do **not** treat a per-bin WoE as a "mean" and average it across cohorts — it is a function
of the bin's good/bad counts, not a sample mean, and its cohort estimates are correlated
through the shared population totals. Instead work with **contrasts between bins**, because
the shared term cancels and leaves a quantity with a textbook sampling distribution.

For bin $i$, $WoE_i = \ln\frac{\%goods_i}{\%bads_i} = \ln\frac{goods_i/G}{bads_i/B}$. The
difference between two bins is therefore a plain 2×2 **log odds-ratio**:

$$
WoE_j - WoE_i = \ln\!\frac{goods_j/bads_j}{goods_i/bads_i} = \ln(OR_{j:i})
$$

the $\ln(G/B)$ population term drops out. That is the whole trick: bin comparisons are log
odds-ratios, so we get Woolf standard errors, Wald CIs, and meta-analysis heterogeneity tests
for free.

## Question 1 — are the bins genuinely different?

**Do the inference on the pooled sample, not per cohort** (per-cohort is underpowered — see
below). Two complementary reads:

**(a) A CI on each bin's WoE.** Woolf standard error, with the correction for the shared
totals:

$$SE(WoE_i) = \sqrt{\tfrac{1}{goods_i} + \tfrac{1}{bads_i} - \tfrac{1}{G} - \tfrac{1}{B}}$$

95% CI $= WoE_i \pm 1.96\,SE$. Bins whose CIs don't overlap are cleanly separated.

**(b) A test on each adjacent contrast.** $\Delta WoE = WoE_j - WoE_i = \ln(OR)$ with

$$SE(\Delta WoE) = \sqrt{\tfrac{1}{goods_i} + \tfrac{1}{bads_i} + \tfrac{1}{goods_j} + \tfrac{1}{bads_j}}, \qquad z = \frac{\Delta WoE}{SE}$$

Testing only **adjacent** pairs (K−1 comparisons) keeps multiplicity mild and matches the
ordinal structure. For the overall monotone signal, prefer a **trend test**
(Cochran–Armitage, or an ordinal logistic regression on the bin rank) over an omnibus K×2
$\chi^2$ — it is more powerful when risk is expected to be monotone in the score.

### Result — `score_klavi_2` (pooled, N = 24,148)

| bin | goods | bads | WoE | 95% CI |
|---|---|---|---|---|
| ≤484 | 1975 | 268 | −0.167 | [−0.29, −0.05] |
| 484–516 | 1983 | 211 | +0.077 | [−0.06, +0.21] |
| 516–603 | 5073 | 477 | +0.200 | [+0.12, +0.28] |
| >603 | 1044 | 58 | +0.726 | [+0.47, +0.99] |

| adjacent contrast | ΔWoE (=lnOR) | z | p |
|---|---|---|---|
| ≤484 → 484–516 | +0.243 | 2.5 | 0.013 |
| 484–516 → 516–603 | +0.124 | 1.4 | **0.15 — not significant** |
| 516–603 → >603 | +0.526 | 3.7 | 0.0002 |

**Read:** the `≤484` and `>603` extremes are solidly separated, but the two **middle bins
(484–516 vs 516–603) are statistically indistinguishable even pooled** (p = 0.15, CIs overlap
heavily). That cut point is not real — the interior should be **merged** into one monotone
bin.

## Question 2 — are the cohort inversions signal or sampling noise?

Frame it as a **fixed-effect meta-analysis**: each cohort $c$ contributes an estimate of the
same contrast, $\theta_c = \Delta WoE_c$, with weight $w_c = 1/SE_c^2$ (Haldane 0.5 added to
each cell so empty cells don't break the SE). The pooled estimate is
$\hat\theta = \frac{\sum w_c\theta_c}{\sum w_c}$, and **between-cohort heterogeneity** is

$$Q = \sum_c w_c(\theta_c - \hat\theta)^2 \ \sim\ \chi^2_{C-1}, \qquad I^2 = \max\!\left(0, \frac{Q - (C-1)}{Q}\right)$$

Under $H_0$ "the contrast is constant across cohorts", $Q$ equals its df in expectation and
$I^2 = 0$. A large $Q$ / high $I^2$ means the cohort estimates vary **more** than sampling
error allows — genuine instability. A small $Q$ / $I^2 \approx 0$ means the wobble (inversions
included) **is** sampling noise. Equivalent GLM form: fit
$\text{logit}(bad) \sim \text{bin} \times \text{cohort}$ and **likelihood-ratio-test the
interaction** — non-significant interaction ⇒ bin effects are stable.

### Result — `score_klavi_2` (13 cohorts)

| adjacent contrast | pooled ΔWoE | Q (df = 12) | p | I² | inverted cohorts |
|---|---|---|---|---|---|
| ≤484 → 484–516 | +0.237 | 7.1 | 0.85 | 0% | 3/13 |
| 484–516 → 516–603 | +0.178 | 12.6 | 0.40 | 4% | 4/13 |
| 516–603 → >603 | +0.432 | 5.0 | 0.96 | 0% | 0/13 |

**Read:** every $Q$ is below its df, all p ≥ 0.4, $I^2 \approx 0$ — **zero excess
heterogeneity.** The cohort-to-cohort variation, including all 7 inversions, is entirely
consistent with binomial sampling noise. The ordering is *not* genuinely unstable.

## Question 3 — a per-cohort discrimination diagnostic

A complementary, per-cohort view: instead of one contrast at a time, ask "**does the score
separate risk at all in month $c$?**" — a K×2 test of the bin × {good, bad} table within each
cohort. Two versions:

- **Pearson $\chi^2$** (df = K−1 = 3) — the omnibus independence test. It ignores the bin
  ordering, so it is underpowered for a monotone score, and it needs expected cell counts
  $\gtrsim 5$ to be trustworthy (the top `>603` bin has only ~4–5 bads per cohort, so this bites).
- **Cochran–Armitage trend** (df = 1, scores 1…K on the ordered bins) — tests specifically for
  a *monotone* trend in bad rate. This is the correct primary test for an ordinal score and is
  markedly more powerful.

### Result — `score_klavi_2`, per cohort

Significant discrimination at $\alpha = 0.05$:

| test | count | cohorts |
|---|---|---|
| Pearson $\chi^2$(3) | **3 / 13** | 202410, 202411, 202506 |
| Cochran–Armitage trend | **6 / 13** | 202406, 202410, 202411, 202501, 202502, 202506 |
| not significant | 7 / 13 | 202407, 202408, 202409, 202412, 202503, 202504, 202505 |

(202412 and 202505 sit right at the boundary, p ≈ 0.052; 202409 even trends the *wrong* way,
z = +1.2 — one of the visual "inversion" months.)

Three readings, which are the point of the exercise:

1. **The trend test nearly doubles the detections (3 → 6)** — using the ordinal structure
   recovers the power the omnibus $\chi^2$ throws away. Reporting only the $\chi^2$ would
   understate how often the score works.
2. **"Not significant" ≠ "no signal" — it is low power.** With ~18 bads/bin and expected cells
   as low as 1.4, most single cohorts cannot reach significance even though the *pooled* trend
   is overwhelming (`>603` contrast z = 3.7). The non-significant months are exactly the thin,
   noisy ones — including the visual inversions — not counter-evidence to the signal.
3. **Small cells and multiplicity.** Several cohorts have expected counts < 5, so their
   *Pearson* p-values are approximate (202406: $\chi^2$ misses at 0.081, the exact-friendlier
   trend test catches it at 0.013). And 13 tests at 0.05 expect ~0.65 false positives; only
   202410 / 202411 (p < 0.001) survive a Bonferroni/FDR correction — so treat the counts as a
   descriptive power diagnostic, not a claim that "6 months truly discriminate."

The verdict matches Questions 1–2: the score discriminates in about half the months and is
merely **underpowered** (not broken) in the rest — so, again, **pool for inference.**

## Why per-cohort inference is hopeless here

The median cohort holds **≈ 18 bads per bin**. A per-cohort WoE therefore carries

$$SE \approx \sqrt{\tfrac{1}{158} + \tfrac{1}{18}} \approx 0.25 \ \Rightarrow\ \pm 0.49 \text{ at } 95\%.$$

The true adjacent gaps are 0.12–0.53 — *smaller than the noise band* — so sign flips between
neighbouring bins are **expected**, not evidence of instability. This is why the trustworthy
reads are pooled significance (Q1) and cross-cohort heterogeneity (Q2), never a single
month's WoE.

## Conclusions for `score_klavi_2`

- **The inversions are a low-volume artifact** (I² = 0), not instability — the risk ordering
  is reliable once you stop reading it month by month.
- **The two middle bins are not distinguishable even pooled** — a real, separate finding. The
  remedy is to **merge 484–516 with 516–603** into one monotone interior bin. That single
  re-bin also eliminates 4 of the 7 cohort inversions by construction, which is exactly the
  "coarser / monotone" fix the 2.0 §6 note gestured at — now with a test behind it.
  **Applied**: `references/bin_spec.yaml` now sets `score_klavi_2.cuts: [484, 603]` (3 bins
  `≤484 | 484–603 | >603`); notebooks 2.x/3.1 were re-run against it, and the merged scheme's
  adjacent boundaries are both highly significant (z = 4.3 and 4.0).

## The generalizable recipe

1. **Contrasts, not raw WoE means** — compare bins via the log-OR; it has a clean Woolf SE and
   cancels the shared population term.
2. **"Bins distinct?"** → per-bin and adjacent-pair CIs on the **pooled** sample; ordinal
   trend test for the overall monotone signal.
3. **"Inversions real?"** → Cochran's Q + I² across cohorts, or the equivalent
   `bin × cohort` logistic interaction LR-test.
4. **Always pool for inference** — per-cohort is underpowered by construction.
5. **Caveats**: Haldane 0.5 for empty cells; cluster on `uuid` (or dedupe as in 2.2 §5) since
   re-applications break the independence the SEs assume; and the whole analysis inherits the
   `Contratado`-only selection bias (`references/information-value.md`).

---

*Reproducibility note.* Figures above were computed directly from
`data/interim/applications.parquet` with the `references/bin_spec.yaml` bins. The project conda
env has no `scipy`, so p-values used closed-form tail approximations (`math.erfc` for the
normal, Wilson–Hilferty for $\chi^2$); values are accurate to the reported precision. WoE
point estimates use the project's 0.5 smoothing; the SEs above use raw (Haldane-corrected)
counts, as the variance formulas require.

# Information Value (IV) & Weight of Evidence (WoE)

Reference for the univariate signal analysis (notebook 2.0). In this project, "bad" means
`OVER30M2 = 1` and "good" means `OVER30M2 = 0`, always on the labeled `Contratado` sample.

## What IV is

**IV (Information Value)** is a classic credit-scoring statistic that measures how well one
variable, by itself, separates goods from bads. It is built on top of **WoE (Weight of
Evidence)**, so the two always come as a pair.

## How it works

Bin the variable (deciles for numerics, categories for categoricals, **missing as its own
bin**). For each bin $i$:

$$WoE_i = \ln\left(\frac{\%\,goods_i}{\%\,bads_i}\right)$$

where $\%\,goods_i$ is the share of *all* goods that fall in bin $i$, and $\%\,bads_i$ the
share of all bads. WoE is positive where goods are over-represented (low-risk bin), negative
where bads concentrate (high-risk bin), zero where the bin looks like the population. Then:

$$IV = \sum_i (\%\,goods_i - \%\,bads_i) \times WoE_i$$

Each term is $\geq 0$ (both factors always share the same sign), so $IV \geq 0$: it
accumulates separation across bins regardless of direction.

## Worked mini-example

Suppose a `score_klavi_2` decile holds 5% of the goods but 15% of the bads:
$WoE = \ln(5/15) \approx -1.10$, contribution $= (0.05 - 0.15) \times (-1.10) \approx 0.11$ —
one risky decile alone already yields a "medium" IV.

## Reading the number

Conventional thresholds:

| IV | Verdict |
|---|---|
| < 0.02 | useless |
| 0.02 – 0.1 | weak |
| 0.1 – 0.3 | medium |
| 0.3 – 0.5 | strong |
| > 0.5 | suspicious — too good, check for leakage |

The last row is why the plan pairs IV with a leakage screen: a variable that "predicts"
default too well often encodes information from after the decision.

## Why it fits this project

- **Missing data is a first-class citizen** — NaN gets its own bin and its own WoE. With our
  segments (48% no snapshot, 95.5% no open finance), the "missing" bin's WoE tells us whether
  *not having Klavi data is itself predictive* — exactly the phase-2 question.
- **Pre-model and monotone-friendly** — no model fit needed, and the WoE-by-bin profile shows
  the *shape* of the risk relationship (monotone? U-shaped?), which is what you need to set
  explainable policy cutoffs in phase 3.
- **Comparable across variables** — one number per variable gives the ranking the client
  asked for ("which variables are most relevant for predicting default").

## Caveats

- **Binning sensitivity**: IV depends on the binning choice; too many bins with few bads
  inflates it. Enforce a minimum bin count, and use a smoothing constant when a bin has zero
  goods or zero bads (avoids $\ln(0)$).
- **Univariate only**: two high-IV variables can be redundant — the correlation/redundancy
  step handles that.
- **Selection bias**: on this data IV is computed on contracted loans only; the
  reject-inference caveat applies to every IV reported.

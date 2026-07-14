# Population Stability Index (PSI) & the stability screen

Reference for the stability analysis (notebook 2.2 shortlist validation, §3; machinery in
`credit_policy.woe.psi`). It runs on the same WoE bins as the IV analysis
(see `references/information-value.md`), always on the labeled `Contratado` sample.

## What PSI is

**PSI (Population Stability Index)** measures how much a variable's *distribution* has moved
between two populations — here, one `SAFRA` (application-month cohort) versus a pooled
reference. It answers "is the mix of applicants in each bin still the same?", not "does the
variable still predict?". Those are different questions, which is why the screen pairs PSI
with **IV computed per cohort** (does the signal hold) — the two together decide whether a
variable is durable or a one-month artifact.

## How it works

Bin the variable exactly as for WoE (**missing is its own bin**). Take the bin-count vector
of the reference population (`expected`, $e_i$) and of the cohort (`actual`, $a_i$), align
them on the union of bins, convert to shares, and sum:

$$PSI = \sum_i (a_i\% - e_i\%)\,\ln\!\left(\frac{a_i\%}{e_i\%}\right)$$

Each term is $\geq 0$ (the sign of $a_i\% - e_i\%$ always matches the sign of
$\ln(a_i\%/e_i\%)$), so $PSI \geq 0$ and it accumulates drift across bins regardless of
direction. It is **symmetric** — swapping `expected` and `actual` gives the same value — so
"expected vs actual" is just a labelling convention. Identical distributions give exactly 0.

As with WoE, a **0.5 smoothing** constant is added to every bin count before normalizing
(`eps=0.5` in `woe.psi`), so an empty bin in one population can't force a division or log of
zero.

## Worked mini-example

Suppose a bin holds 30% of the pooled reference but 40% of one cohort:
$(0.40 - 0.30)\times\ln(0.40/0.30) \approx 0.10 \times 0.288 \approx 0.029$ — one shifted bin's
contribution. A few bins moving that much together push a variable toward the 0.1 "moderate"
band.

## Reading the number

Conventional thresholds:

| PSI | Verdict |
|---|---|
| < 0.1 | stable |
| 0.1 – 0.25 | moderate shift |
| > 0.25 | significant shift |

In this project (2.2 §3), three of the four shortlist variables are comfortably stable
(PSI max ≈ 0.02–0.03 across cohorts). **`score_klavi_2` is the exception**: its PSI peaks at
**0.32** in one vintage (a significant shift) and its within-cohort IV swings widely — so it
stays on the shortlist but is **flagged "watch"**, to be revisited (coarser/monotone bins or a
recency guard) before phase-3 policy leans on it.

## Why it fits this project

- **Same bins, missing included** — PSI runs on the WoE bins, so the `(missing)` category is a
  first-class bin. A shift in *how often Klavi data is available* (48% no snapshot) shows up as
  drift in that bin, not as a silent gap.
- **Pre-model and cheap** — no model fit; one number per variable per cohort, computed straight
  from bin counts, so every candidate can be screened cohort by cohort.
- **Separates drift from decay** — PSI catches a moving population even when average risk looks
  flat; pairing it with per-cohort IV catches signal that fades even when the population is
  steady. A variable must pass both to be trusted.

## Caveats

- **Binning must match**: PSI is only meaningful when both populations use the *same* bin
  edges; re-binning between reference and cohort makes the number uninterpretable.
- **Thin-cohort noise**: small `SAFRA` cohorts make bin shares jumpy and inflate PSI. The 0.5
  smoothing tames division/log blow-ups but does not remove sampling noise — read a single
  cohort's spike against the trend, not in isolation.
- **Drift ≠ signal loss**: a high PSI flags a population change, not necessarily worse
  prediction (the variable may still separate goods from bads inside the new mix). This is
  exactly why the screen reads PSI and per-cohort IV together, never PSI alone.
- **Selection bias**: like IV, PSI here is computed on contracted loans only; drift in the
  rejected population is unobserved.

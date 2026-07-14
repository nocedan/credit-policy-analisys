# Worked example — how a large `(missing)` bin behaves in IV and PSI

A didactic companion to `references/information-value.md` (IV/WoE) and
`references/population-stability.md` (PSI). It works one small 3-bin example all the way
through, showing the **per-bin contributions**, to make concrete why keeping the
`(missing)` bin in changes both statistics — and why it does so honestly for IV but only
conditionally for PSI. Motivation: in this project ~48–49% of applications carry no Klavi
snapshot, so the `(missing)` bin is the single largest bin in almost every variable.

## Setup

Sample = **1,000 labeled rows** (`Contratado`). Missing is **50%** of the book and is made
**non-discriminative** — its bad rate equals the overall mean (10%) — while the two 25%
bins discriminate hard.

| bin | rows | bads | goods | bad rate |
|---|---|---|---|---|
| `(missing)` | 500 | 50 | 450 | **10%** ← = overall mean |
| `low` (safe) | 250 | 10 | 240 | 4% |
| `high` (risky) | 250 | 40 | 210 | 16% |
| **total** | 1000 | 100 | 900 | 10% |

`G = 900` goods, `B = 100` bads. (Un-smoothed throughout; the 0.5 smoothing used in
`woe.py` shifts nothing at these counts.)

## IV, missing kept in

`WoEᵢ = ln(%goodsᵢ / %badsᵢ)`, `contribᵢ = (%goodsᵢ − %badsᵢ)·WoEᵢ`

| bin | %goods | %bads | WoE | contribution |
|---|---|---|---|---|
| `(missing)` | 450/900 = .500 | 50/100 = .500 | ln(1) = **0** | (.500−.500)·0 = **0.0000** |
| `low` | 240/900 = .267 | 10/100 = .100 | ln(2.667) = +0.981 | (.267−.100)·.981 = **0.1635** |
| `high` | 210/900 = .233 | 40/100 = .400 | ln(0.583) = −0.539 | (.233−.400)·(−.539) = **0.0898** |
| | | | **IV** | **0.2533** (medium) |

The 50% missing bin contributes **exactly 0**: its bad rate sits at the mean, so
`%goods ≈ %bads` **and** `WoE ≈ 0` — both factors vanish together. All IV comes from the two
25% bins.

## PSI, missing share stable, non-missing mass drifts

PSI compares two populations by bin *share* (not good/bad). Reference vs one cohort; missing
holds at 50%, the non-missing half shifts low→high (a riskier intake):

`contribᵢ = (aᵢ% − eᵢ%)·ln(aᵢ%/eᵢ%)`

| bin | e% (ref) | a% (cohort) | ln(a/e) | contribution |
|---|---|---|---|---|
| `(missing)` | .50 | .50 | ln(1) = **0** | (.50−.50)·0 = **0.0000** |
| `low` | .25 | .15 | ln(0.6) = −0.511 | (.15−.25)·(−.511) = **0.0511** |
| `high` | .25 | .35 | ln(1.4) = +0.336 | (.35−.25)·(+.336) = **0.0336** |
| | | | **PSI** | **0.0847** (stable, < 0.1) |

The stable 50% bin again contributes **0** — it pins half the mass, so only the moving half
generates drift.

## The `(1 − f)` scaling — drop the missing anchor

Take the *same* behavioral shift but renormalize to the non-missing bins only (`f` = missing
fraction = 0.5).

**PSI** (ref 50/50 → cohort 30/70, the identical relative move):

| bin | e% | a% | ln(a/e) | contribution |
|---|---|---|---|---|
| `low` | .50 | .30 | −0.511 | **0.1022** |
| `high` | .50 | .70 | +0.336 | **0.0673** |
| | | | **PSI** | **0.1695** (moderate) |

PSI **doubles** (0.085 → 0.170), crossing stable → moderate. Doubling each share turns
`(a−e)·ln(a/e)` into `2(a−e)·ln(a/e)`, so a stable missing fraction `f` scales the whole PSI
by `(1 − f)`.

**IV** (recompute on the 500 non-missing rows: `G = 450`, `B = 50`):

| bin | %goods | %bads | WoE | contribution |
|---|---|---|---|---|
| `low` | 240/450 = .533 | 10/50 = .200 | ln(2.667) = **+0.981** | (.533−.200)·.981 = **0.3269** |
| `high` | 210/450 = .467 | 40/50 = .800 | ln(0.583) = **−0.539** | (.467−.800)·(−.539) = **0.1797** |
| | | | **IV** | **0.5066** |

IV also **doubles** (0.2533 → 0.5066), and note **every WoE is unchanged** (+0.981, −0.539).
Removing an at-mean bin halves `G` and `B` by the *same* factor, so `%goods` and `%bads` each
double but their ratio — hence `WoE` — is untouched; only the `(%goods − %bads)` weight scales
up.

So both statistics obey the same rule:

```
IV_incl(missing)  =  (1 − f) · IV_excl(missing)      →  0.5066 × 0.5 = 0.2533
PSI_incl(missing) =  (1 − f) · PSI_excl(missing)     →  0.1695 × 0.5 = 0.0847
```

## Takeaways

- **A large at-mean `(missing)` bin is inert in IV and damps PSI** — 0 contribution in both,
  and it shrinks the total by `(1 − f)`. It makes a variable look calmer on both axes.
- **The damping is honest for IV, conditional for PSI.** IV shrinks because size *forces* the
  missing bad rate toward the mean (`p_m − mean = (1 − f)(p_m − p_r)`), so it is genuinely
  non-discriminating. PSI shrinks *only while the missing share itself stays put* — if Klavi
  coverage drifted over time, that same large bin would become the biggest PSI contributor.
- **The clean doubling of IV holds only because missing is at the mean.** A discriminative
  missing bin would shrink `G` and `B` by *different* factors, re-basing the reference odds and
  shifting every WoE — no clean `(1 − f)` scaling.
- **Which IV to report:** the full-sample **0.253** (missing kept in) is the one the plan uses —
  it charges the variable for the half it can't see. The present-only **0.507** is its power
  *where it exists*, but ranking on it would reward a separator you observe only half the time.
  Same variable, 0.507 on paper, 0.253 once coverage is priced in — the "coverage before
  signal" rule in one number.

# Key Takeaways per Notebook

One section per notebook. Persisted here on request once each notebook is finished.

## 1.0 — Initial Data Exploration

- Misleading file names: `profile_*` holds **performance**, `transactions_*` holds **application
  features**. Business key: `uuid` + application date, unique in both tables.
- Only **52%** of applications have a feature snapshot at decision time, uniform across `STATUS`
  (Aprovado 48.1%, Contratado 48.5%, Reprovado 47.9% missing) — availability doesn't differ by
  outcome. Within that, coverage splits in two tiers: broad variables miss ~54%, the open-finance
  trio (`score_klavi_1`/`Renda`/`risco_aposta`) misses ~95%.
- `OVER30M2` (target) exists only for `Contratado` (24,148 rows; 10.30% default) — **selection
  bias**: a model trained on `Contratado` doesn't generalize directly to the through-the-door
  population.
- Deterioration: default rate rises from ~8–10% (2024 vintages) to 12.5% (202506); approval rate
  falls from ~54% to ~40% over the same period — policy tightened as risk worsened, without
  reversing the rise.
- Sentinels are material: `-999999` in `score_klavi_1` (7.3% of non-null) and
  `status_empregaticio` (3,417 rows); `Capacidade Financeira` has 22,005 negative values (kept as
  real, not sentinel); thin extreme tail in `Renda`.

## 1.1 — Build Interim Application Table

- `data/interim/applications.parquet` written: 220,618 rows, one per application (all `STATUS`),
  `uuid` + `DATA` unique, round-trip verified.
- Cleaning is conservative by design: only provable sentinels → NaN (`score_klavi_1` -999999,
  `status_empregaticio` '-999999'); negative `Capacidade Financeira` kept as valid, only the
  extreme tail flagged. Distribution-shaping (winsorizing) deferred to Fase 2.
- Merge is a simple left join on `uuid` + application date (`REFERENCIA` = `DATA`) — verified
  equivalent to a point-in-time asof rule; 114,689 applications (52.0%) carry a snapshot.
- `has_snapshot` / `has_open_finance` (anchored on `Renda`) added as explicit coverage-segment
  flags for Fase 2.

## 1.2 — Application Multiplicity & Grain

- `(uuid, DATA)` is unique; `(uuid, SAFRA)` is not — 8,305 users re-applied within a single month
  (10,780 rows above the monthly grain), always intra-month by construction.
- `Contratado` evidence: 88 users hold two contracts in one month, always on distinct dates
  (median 7 days apart), 7 with conflicting `OVER30M2` — provably distinct contracts, not
  duplicates.
- Counterfactual dedup upside ≈ **0** (snapshot availability tracks the `uuid`, not the row) while
  the downside is real: 51 groups would lose open-finance, 143 keep a less-complete survivor,
  1,063 hold conflicting feature values.
- **Decision**: keep the `(uuid, DATA)` grain, no dedup. User-level over-representation in
  IV/WoE becomes a Fase 2 weighting decision (resolved in 2.2 §5: negligible impact).

## 2.0 — Binning Workbench

- Turns binning into a hand-tunable, git-tracked artifact: `estimate_spec` seeds
  `references/bin_spec.yaml` from adaptive quantiles (guarded — re-running never overwrites hand
  edits), then per-bin WoE, pooled WoE shape, and WoE-over-`SAFRA` stability drive manual merges
  until each kept variable is both discriminating and stable across vintages.
- Resulting hand-tuned bins: `classe_social` → `A/B/C` vs `D/E`; `status_empregaticio` →
  `Desempregado` folded into `Desconhecido`; `Capacidade Financeira` and `score_klavi_2` cut to
  fewer bins, monotonic and stable.
- `references/bin_spec.yaml` becomes the single source of truth for binning across 2.1 and every
  downstream notebook (including the segment machinery in Fase 3).

## 2.1 — Univariate Signal

- Labeled sample: 24,148 applications, 2,488 bads (10.30% default), 1,417–2,367 rows per safra.
  Coverage in three tiers: flags 100%, broad variables ~46–52%, open-finance trio ~4.5%.
- IV ranking: signal is **modest across the board** — no variable reaches "medium" (0.1).
  `classe_social` 0.091, `Capacidade Financeira` 0.067, `score_klavi_2` 0.037,
  `status_empregaticio` 0.031, `regiao` 0.025. Nothing near leakage territory (> 0.5). The
  open-finance trio scores near zero (IV ≤ 0.006) **because of 95.5% missingness**, not
  intrinsic weakness — `has_snapshot` alone has IV 0.016.
- Shortlist frozen in `credit_policy.VAR_SELECTION`: `classe_social`, `Capacidade Financeira`,
  `score_klavi_2`, `status_empregaticio`. `regiao` (next by IV, 0.025) **excluded on fairness
  grounds** — proxies protected attributes (redlining / disparate-impact risk).

## 2.2 — Shortlist Validation

Four sanity checks on the frozen shortlist before building a policy on it:

- **Redundancy**: all four are genuinely different signal — strongest overlap `classe_social` ×
  `Capacidade Financeira` at 0.39 (under the 0.5 threshold). A naive 0.73 correlation between
  them is an artifact of co-missingness, not real overlap (vanishes once restricted to rows
  where both are observed). **Keep all four** — socioeconomic block + financial block,
  complementary.
- **Stability**: three of four rock-solid across 13 vintages (PSI ≈ 0.02–0.03). `score_klavi_2`
  is the exception — PSI 0.32 in one safra, IV volatile (0.01–0.18) — kept but flagged **"watch"**.
- **Leakage**: none — every candidate is weak-tier (IV < 0.1), and all are point-in-time
  snapshots by construction. Clean.
- **Weighting**: one-row-per-`uuid` drops only 849 of 24,148 rows; IV changes < 0.001, ranking
  unchanged. Robust to the multiplicity flagged in 1.2.
- **Bottom line**: all four variables pass and move to Fase 3; `score_klavi_2` carries a watch
  flag. `regiao`'s fairness exclusion will be tested for residual disparate impact once a policy
  exists (3.3).

## 3.0 — Segment Map & Stock

- Segmentation built and persisted: `segmento` = `classe_social` × `status_empregaticio`, 5 named
  cells + `(missing)`, declared in `references/segment_spec.yaml` and crossed by
  `credit_policy.segments` — reuses the 2.0 WoE/PSI machinery unchanged. Written to
  `data/processed/applications_segmented.parquet`.
- `(missing)` is **half of everything** — 48.6% of the funnel, 49% of the labeled book, 11.5%
  default — and holds almost no score (1.1% vs ~89–90% in named cells): score and demographics
  are co-missing, so a score cutoff is only well-posed on the named cells.
- Named cells order cleanly by risk: three tiers, A/B/C 6.5–7.8%, `(missing)` 11.5%, D/E
  15.5–16.4% (2.4× spread).
- The **current policy misorders** at least one cell: `A/B/C · Formal`, the safest (6.5%), is
  approved less (43.7%) than a riskier A/B/C cell (50.1% at 7.8%) — direct swap-set evidence.
- `D/E · Formal` (22 labeled / 356 total) merged into `D/E · Autônomo/Formal` — too thin for its
  own cutoff.

## 3.1 — Segment Baseline & Score Signal

- Baseline validated: the A/B/C > `(missing)` > D/E risk ordering holds in 74 of 78
  segment×vintage cells (all 4 flips are small-n noise); segment-mix PSI ≤ 0.027 — the
  demographic structure is the stable part of the policy (unlike `score_klavi_2` alone, PSI 0.32).
- Score axis validated: `score_klavi_2` orders risk end-to-end in all 5 named cells; steepest
  inside `D/E · Autônomo/Formal` (21.4% → 6.1%) — per-segment cutoffs beat blanket segment
  denial.
- Missing-score rule made explicit: scoreless applicants **inside** a named segment default at
  that segment's own baseline (no adverse selection, deltas −2.3 to +1.9 pp); the `(missing)`
  segment sits at its own 11.5% baseline, between the A/B/C and D/E tiers.

## 3.2 — Cutoff Simulation & Trade-off

- `(missing)` has no score or demographics to condition a cutoff on, so it's excluded from the
  τ-sweep and instead deferred to whatever the client already decided (`mode: keep_current`:
  approve iff `STATUS ∈ {Aprovado, Contratado}`) — a fixed floor (49% of the book, 11.5%
  descriptive) present at every τ, not a manufactured decision.
- The resulting frontier is non-monotonic (dips before it rises): tight τ first admits tiny,
  very-safe named slivers that dilute the floor below 10%, before larger and riskier named
  volume pulls it back toward the unconditional 10.3%.
- Operating point **τ\* = 11.5%** → keeps 90% of the book at **9.64%** (vs 10.30% baseline); the
  removed 10% defaults at 16.3%. Rules: A/B/C no score gate; D/E score ≥ 595 / ≥ 518, scoreless
  denied; `(missing)` deferred. Persisted to `references/policy_v1.yaml`.
- Extrapolation to unlabeled stock kept bounded and separated by evidence: named-segment rules
  would admit 36.1% of `Reprovado` (43.1k) at an assumed ~7.4% — a real but bounded hypothesis;
  `(missing)`'s 57.8k `Reprovado` stay denied (no hypothesis asked of the one segment with zero
  conditioning variables). Recommendation: adopt named-segment cutoffs on current intake, expand
  into named-segment `Reprovado` only via a staged, monitored test.

## 3.3 — Fairness / Disparate Impact

- No residual disparate impact by `regiao`; disparity **narrows** under `policy_v1` — four-fifths
  ratio 0.832 → 0.931. Current-policy gap: Nordeste 42.3% vs Norte 50.9% approval; under
  `policy_v1` the spread compresses to 72.1–77.5%, tracking measured regional risk (Nordeste
  11.2% vs Sul 6.2% default) rather than region itself.
- Caveats: test limited to the region-known ~52% of the funnel; proposed approvals are simulated
  under the 3.2 transfer hypothesis — re-run on realized approvals once the policy or its staged
  test goes live.
- **Fase 3 complete**: segmentation (3.0) → validated baseline & score axis + missing-score rule
  (3.1) → cutoff frontier & operating point `policy_v1.yaml` (3.2) → fairness check passed (3.3).

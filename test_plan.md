# Test Plan — Modularize & Test the Statistical Core

## Context

The deck's every quantitative claim flows through two dependency chains:

- **Signal chain (Q1/Q2):** `VAR_SELECTION` → `binning` → `woe` (IV, PSI, WoE-corr)
- **Policy chain (Q3):** `binning` + `segments` → `policy` + notebook `policy_at` τ-sweep


---


## pytest coverage, ordered by priority (most-used → least-used)

Priority proxy = number of notebooks / result-chains depending on the module.
Add one `tests/test_<module>.py` per item; all fixture-based.

- [ ] **1. `woe.py`** — statistical core (5 notebooks; both chains)
  - [X] `woe_table`: bins partition sample; `iv_contrib ≥ 0`; empty bins kept; 0.5 smoothing; known WoE on a 2×2 fixture
  - [ ] `iv_of`: sums occupied bins only; matches hand-computed IV
  - [ ] `iv_verdict`: each threshold boundary (useless / weak / medium / strong / suspicious)
  - [ ] `woe_over_time`: `min_n` masks low-count bins to NaN; shape = safras × bins
  - [ ] `woe_encode` / `woe_frame`: per-row value equals its bin WoE; numeric dtype; one col per var
  - [X] `psi`: 0 for identical (have it); grows under shift; smoothing avoids inf/div0

- [ ] **2. `binning.py`** — feeds all WoE/IV/PSI (5 notebooks)
  - [X] `apply_spec` numeric: correct edges; NaN → `(missing)`; order stable; labels
  - [X] `apply_spec` categorical: group mapping; unlisted → `(outros)`; NaN → `(missing)`; category order
  - [ ] `estimate_spec`: rare-category drop (`min_share`); `n_bins` clamp; monotone int cuts
  - [ ] `_round_int_cuts`: strictly increasing; collapses dups
  - [ ] `transform`: one column per spec variable
  - [ ] `save_spec` / `load_spec`: round-trip via `tmp_path`

- [ ] **3. `segments.py`** — builds `segmento` (3.0; consumed in 3.1/3.2)
  - [X] `apply_segment`: cell label `<bin> · <bin>`; missing-in-any-dim → `(missing)`; product order
  - [ ] `_full_groups`: partial merge completed with identity groups; product order preserved
  - [ ] `make_segments`: one column per segmentation

- [ ] **4. `policy.py`** (incl. extracted sweep) — policy chain (3.2)
  - [X] `approve`: `score_min` gate; `None` = approve all scored; `.inf` denies scored; scoreless approve/deny; `keep_current` = STATUS ∈ {Contratado, Aprovado}
  - [ ] `save_policy`: round-trip via `tmp_path`
  - [X] `sweep_tau`/`policy_at`: floor always kept; cutoff monotonic in τ; correct kept counts; edge τ (0.0 and max)
  
---

## Verification

- [ ] `conda run -n credit-policy pytest -q` — all green (recall `PYTHONNOUSERSITE=1` is
  set in the env so the stray user-site pytest doesn't shadow it)
- [ ] Notebooks 3.2 and 1.0 re-execute headlessly with unchanged figures/numbers after extraction
- [ ] Optional: `pytest --collect-only` to confirm all six new files are discovered

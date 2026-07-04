# Key Takeaways per Notebook

One section per notebook. Updated as the analysis progresses.

---

## 1.0 — Initial Data Exploration (`notebooks/1.0-dn-initial-data-exploration.ipynb`)

**What was done**: first contact with the two raw files — schemas, grain/keys, join coverage, target definition, data quality, feature distributions, and a directional look at features vs. target.

### Data structure

- File names are misleading: `profile_case_credit.parquet` holds **performance/target data** (`SAFRA`, `OVER30M2`, `STATUS`); `transactions_case_credit.parquet` holds **application features** (Klavi scores, demographics, income).
- **Neither table is unique on `uuid`**: perf = 220,618 rows / 184,009 uuids (repeat applications); feat = 371,596 rows / 96,196 uuids (~3.9 feature snapshots per person, keyed by `REFERENCIA`).
- A naive join explodes to **1.38M rows** → a point-in-time snapshot rule (latest `REFERENCIA ≤ DATA`) is required to build the modeling table without leakage.

### Target & selection bias

- `OVER30M2` exists **only for `STATUS = Contratado`** — 24,148 rows, **10.30% default rate**. `Aprovado` (77k) and `Reprovado` (119k) have no performance → **reject-inference / selection-bias** problem for any model trained on contracted clients.
- Default rate **rises across vintages**: ~8–10% (2024) → ~12.5% (202506). Either real deterioration or immature performance in recent safras — pending client confirmation of the observation window.

### Coverage & data quality

- **47.7% of applications have no Klavi features at all** — coverage is itself a policy design constraint.
- Missingness is structural: `score_klavi_1`, `Renda`, `risco_aposta` are missing **together** in 91.3% of rows (likely open-finance consent), while `score_klavi_2` (~89% coverage) and `Capacidade Financeira` (~88%) are broadly available → the practical policy candidates.
- Sentinel/invalid values: `score_klavi_1` contains **-999999** sentinels (real range ~0–100); `Capacidade Financeira` has extreme negatives (min ≈ -1.09M).
- Dtypes to fix: `DATA`/`REFERENCIA` are date strings; `SAFRA` is float (202408.0).

### Open questions for the client

1. Exact definition/observation window of `OVER30M2`; is performance mature for safras 202505–202506?
2. What distinguishes `Aprovado` from `Contratado`? Was `score_klavi_2` already used in the current policy?
3. Why do 47.7% of applications lack Klavi features (consent funnel, integration date, extraction issue)?
4. Which `REFERENCIA` snapshot is available at decision time?

---

## 1.1 — Data Cleaning *(planned)*

*(takeaways to be added)*

## 2.0 — Feature Analysis *(planned)*

*(takeaways to be added)*

## 3.0 — Scorecard & Policy Rules *(planned)*

*(takeaways to be added)*

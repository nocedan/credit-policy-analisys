# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Credit Policy Analysis

Credit-granting policy review using Klavi's variables. Pure analysis repo — notebooks plus markdown docs; there is no build, lint, or test tooling.

**Information flow** (cyclic — notebook conclusions feed back into the plan):

`docs/case-scenario.md` (the brief) → `docs/analysis-plan.md` (phased plan + working conventions) → `notebooks/` (the work) → `reports/key_takeaways.md` (findings) → back to plan.

The presentation deck extends that chain: `reports/key_takeaways.md` + `docs/case-scenario.md` §"Answers" + `notebooks/` → `reports/presentation-outline.md` (slide-by-slide key messages, bullets, figure refs) → `reports/presentation.md` (the Marp deck itself) → `reports/presentation.html` / `reports/presentation.pdf` (rendered outputs) and `README.md` (a plain-markdown copy of the deck: no Marp/HTML, figure paths prefixed `reports/`, and every "Klavi" mention anonymized — `klavi` → `open_finance_bureau` in identifiers, "open finance bureau" in prose; figures untouched). Keep numbers reconciled with `key_takeaways.md`; keep `presentation.md` in sync with `presentation-outline.md` when either changes.

Start any session by reading the plan and the takeaways; each doc owns its own detail — don't duplicate it here.

## Environment & running

- Conda env: `credit-policy` (python 3.12, pandas, seaborn, pyarrow, jupyterlab).
- Run snippets with `conda run -n credit-policy python ...`; execute a notebook headlessly with
  `conda run -n credit-policy jupyter nbconvert --to notebook --execute --inplace notebooks/<name>.ipynb`.
- Notebooks resolve the project root as `Path.cwd().parent`, so execute them with `notebooks/` as the working directory.
- The `credit_policy` package is an editable install in the env (`pip install -e . --no-deps`), so `import credit_policy` works without the `sys.path` hack.
- Run tests with `conda run -n credit-policy pytest -q`. The env sets `PYTHONNOUSERSITE=1` (via `conda env config vars`) so it ignores `~/.local/lib/python3.12/site-packages` — otherwise a stray user-site pytest there shadows the env's copy on `sys.path` and breaks the run.

## Data

- `data/` is not in git. Never modify `data/raw`; derived tables go to `data/interim` → `data/processed`.
- The two raw file names are misleading: `profile_case_credit.parquet` holds **performance** (`uuid`, `DATA`, `SAFRA`, target `OVER30M2`, `STATUS`); `transactions_case_credit.parquet` holds **application features** (`uuid`, `REFERENCIA`, Klavi scores, demographics). Business key: `uuid` + application date.

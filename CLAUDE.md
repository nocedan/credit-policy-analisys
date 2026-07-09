# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Credit Policy Analysis

Credit-granting policy review using Klavi's variables. Pure analysis repo — notebooks plus markdown docs; there is no build, lint, or test tooling.

**Information flow** (cyclic — notebook conclusions feed back into the plan):

`docs/case-scenario.md` (the brief) → `docs/analysis-plan.md` (phased plan + working conventions) → `notebooks/` (the work) → `reports/key_takeaways.md` (findings) → back to plan.

Start any session by reading the plan and the takeaways; each doc owns its own detail — don't duplicate it here.

## Environment & running

- Conda env: `credit-policy` (python 3.12, pandas, seaborn, pyarrow, jupyterlab).
- Run snippets with `conda run -n credit-policy python ...`; execute a notebook headlessly with
  `conda run -n credit-policy jupyter nbconvert --to notebook --execute --inplace notebooks/<name>.ipynb`.
- Notebooks resolve the project root as `Path.cwd().parent`, so execute them with `notebooks/` as the working directory.

## Data

- `data/` is not in git. Never modify `data/raw`; derived tables go to `data/interim` → `data/processed`.
- The two raw file names are misleading: `profile_case_credit.parquet` holds **performance** (`uuid`, `DATA`, `SAFRA`, target `OVER30M2`, `STATUS`); `transactions_case_credit.parquet` holds **application features** (`uuid`, `REFERENCIA`, Klavi scores, demographics). Business key: `uuid` + application date.

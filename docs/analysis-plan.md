# Analysis Plan — Credit Granting Policy Review

**Case**: Fintech client wants to review its credit granting policy using Klavi's variables
(see [case-scenario.md](case-scenario.md)). Deliverable: which variables predict default, which
are practical policy candidates (rules + score), and an objective, justifiable proposal for the
business team — all with a visual, insight-driven approach.

**Working conventions**: cookiecutter-data-science structure; notebooks named
`<phase>.<iteration>-dn-<description>`; raw data never modified in place
(`data/raw` → `data/interim` → `data/processed`); takeaways per notebook in
[reports/key_takeaways.md](../reports/key_takeaways.md).

# O Problema
O cliente da Klavi quer revisar sua política de concessão de cŕedito. Default rate rises from ~8–10% (2024) to 12.5% (202506) while the approval rate falls from ~54% to ~40% — policy tightened as risk worsened.

# Abordagem:
Quais são as dimensões relevantes do problema? Para cada variável, é importante:

A. ter uma clareza da sua distribuição. Talvez verificar a distribuição com a quebra contratado/não contratado.
B. non-missing count (coverage),
C. e da sua relação com o target (IV/WOE). Variáveis com baixa cobertura terão IV naturalmente menores.
D. É de nossa opção, buscar estratégia de binning que seja estável no tempo e que garanta ordenação.
E. A relevância da variável para revisão da política de crédito é definida pelo IV (discriminação + coverage) e pelo seu papel (vai atuar dentro das aplicações aprovadas ou negadas).
F. A correlação após o binning deve ser calculada para evitar redundancia na proposta final.
G. Estruturação de nova política de crédito baseada na análise da discriminação das variáveis dentro e fora das aprovadas.
** Ou seja, se a variável possui boa descriminação dentro das aprovadas e tem boa cobertura nas negadas, pode representar oportunidade de ampliar a concessão.
De qualquer forma, uma política de abertura deve ser conservadora por conta de que
de 202501 em diante o default rate aumenta com inclinação consistente.

H. Refletir sobre estrutura final do uso das variáveis. Score? Lasso?

---

# Step by step

## Phase 0 — Setup

- [x] Conda environment (`credit-policy`: python 3.12, pandas, seaborn, pyarrow, jupyterlab)
- [x] Cookiecutter-style folder structure (without full boilerplate)
- [x] Git repository initialized; data excluded from version control

## Phase 1 — Explore, clean & organize

- [x] **1.0 Initial exploration**: schemas, grain/keys, join coverage, target definition,
      missingness, sentinel values, feature distributions, directional features-vs-target look
- [x] Resolve grain: business key is `uuid` + application date (`DATA` / `REFERENCIA`),
      unique in both tables;
- [x] Identify structural issues: -999999 sentinels, negative `Capacidade Financeira`
      extremes, two-tier coverage (broad vs open-finance-gated variables), target only
      for `Contratado` (expected — only contracted loans have performance), rising
      vintage default rate
- [x] Prototyped in memory in 1.0 (1.1 productionizes, does not re-derive): dtype casts
      at load (`DATA`/`REFERENCIA` → datetime, `SAFRA` → int, `risco_aposta` → categorical)
      and the application-date join (`REFERENCIA` = `DATA`, simple left join — snapshots
      are application-triggered; verified equivalent to a point-in-time asof rule)
- [x] **1.1 Build interim application table**: re-apply dtype casts, sentinels → NaN
      (`score_klavi_1` -999999, `status_empregaticio` '-999999'), keep negative
      `Capacidade Financeira` as valid (flag extremes only), left join on `uuid` +
      application date (`REFERENCIA` = `DATA`) to one row per application (all STATUS),
      coverage/segment flags, key uniqueness asserted, written to `data/interim/`

## Phase 2 — Feature analysis (relevance & representativeness)

- [ ] **2.0 Univariate signal**: IV / WoE per variable (binned), default rate by decile,
      separation plots (KDE/ROC per variable)
- [ ] Missing-data strategy: treat "no Klavi data" (47.7%) and "no open-finance consent"
      (91.3% for score_klavi_1/Renda/risco_aposta) as explicit segments, not just NaN
- [ ] **Stability**: PSI of each variable across SAFRA; signal stability (IV per vintage)
- [ ] Correlation / redundancy between candidates (e.g. score_klavi_2 × Capacidade Financeira)
- [ ] Leakage screening: any variable suspiciously predictive → challenge its
      point-in-time availability

## Phase 3 — Policy proposal (rules + score)

- [ ] **3.0 Candidate policy design**: simple, explainable rules (cutoffs on
      broad-coverage variables) + score-based ranking for the middle band
- [ ] Swap-set analysis vs. current policy (approve/decline changes and their expected
      default impact)
- [ ] Expected approval rate × default rate trade-off curve to let business choose the
      operating point

# Plano de Análise — Revisão da Política de Concessão de Crédito

**Caso**: cliente Fintech quer revisar sua política de concessão de crédito usando as variáveis
da Klavi (ver [case-scenario.md](case-scenario.md)). Entregável: quais variáveis predizem default,
quais são candidatas práticas para a política (regras + score) e uma proposta objetiva e
justificável para o time de negócio — tudo com uma abordagem visual e orientada a insights.

**Convenções de trabalho**: estrutura cookiecutter-data-science; notebooks nomeados
`<phase>.<iteration>-dn-<description>`; dados raw nunca modificados no lugar
(`data/raw` → `data/interim` → `data/processed`); takeaways por notebook em
[reports/key_takeaways.md](../reports/key_takeaways.md).

# O Problema

Um cliente Fintech quer revisar sua política de concessão de crédito utilizando as variáveis da Klavi. Como cientista de dados Senior gostaria de entender
quais variáveis efetivamente discriminam risco e reconstruir os critérios de aprovação sobre
bases objetivas. O cenário observado nos dados (notebook 1.0) motiva a revisão:

- **Deterioração recente** — o default rate (`OVER30M2`, 30+ dias de atraso nos 2 primeiros
  meses) sobe de ~8–10% nas safras de 2024 para 12,5% em 202506, com inclinação consistente a
  partir de 202501.
- **Política já endurecida** — em paralelo, o approval rate cai de ~54% (meados de 2024) para
  ~40% (2025): a régua foi apertada à medida que o risco piorou, sem reverter a alta de default.
- **Performance só nos contratados** — apenas ~24 mil dos ~221 mil pedidos são `Contratado` e
  têm target observável (10,3% de default); `Aprovado` e `Reprovado` nunca são rotulados
  (selection bias — um modelo treinado só em contratados não generaliza direto para a população
  through-the-door).
- **Cobertura simétrica, label assimétrico** — ~52% dos pedidos têm snapshot na data da decisão,
  em dois níveis (amplas `score_klavi_2` / `Capacidade Financeira` ~46%; open-finance
  `score_klavi_1` / `Renda` / `risco_aposta` ~4,5%) e praticamente idêntica dentro e fora dos
  contratados. O viés está no label, não na disponibilidade das variáveis — logo a cobertura é
  representativa da população through-the-door e a política é aplicável ao funil inteiro.

# Abordagem

Quais são as dimensões relevantes do problema? A análise avança **variável a variável** e, em
seguida, **da variável para a política**.

**Por variável**

1. **Distribuição** — entender a forma; quando útil, quebrar por contratado / não-contratado.
2. **Coverage** — non-missing count; variáveis com baixa cobertura terão IV naturalmente menor.
3. **Relação com o target** — IV / WoE.
4. **Binning** — estratégia estável no tempo e que garanta ordenação (monotonicidade).
5. **Relevância** — definida pelo IV (discriminação + coverage).
6. **Redundância** — correlação pós-binning entre candidatas, para não repetir sinal na proposta final.

**Da variável à política**

7. **Nova política** — estruturar a concessão a partir da discriminação das variáveis. Essa
   discriminação só é **mensurável dentro das `Contratadas`** (única amostra com target); como
   extrapolá-la com segurança para `Aprovado` e `Reprovado` — que não têm target — é o problema
   central da Fase 3, não algo observável agora.
   - A abertura deve ser conservadora: de 202501 em diante o default rate cresce com inclinação
     consistente.
   - Garantir estabilidade temporal das features e binning utilizadas na nova política.
   - Garantir segurança para tomada de decisão a partir do viés de seleção na amostra de treino (vs inferência).

8. **Forma final** — como combinar as variáveis? Score? Lasso?

---

# Passo a passo

## Fase 0 — Preparação

- [x] Ambiente Conda (`credit-policy`: python 3.12, pandas, seaborn, pyarrow, jupyterlab)
- [x] Estrutura de pastas estilo cookiecutter (sem o boilerplate completo)
- [x] Repositório Git inicializado; dados excluídos do controle de versão

## Fase 1 — Explorar, limpar e organizar

- [x] **1.0 Exploração inicial**: schemas, grain/chaves, coverage do join, definição do target,
      missingness, valores sentinela, distribuições das variáveis, visão direcional variáveis-vs-target
- [x] Resolver o grain: a chave de negócio é `uuid` + data da aplicação (`DATA` / `REFERENCIA`),
      única em ambas as tabelas;
- [x] Identificar problemas estruturais: sentinelas -999999, extremos negativos de
      `Capacidade Financeira`, coverage em dois níveis (variáveis amplas vs. variáveis gated
      por open-finance), target apenas para `Contratado` (esperado — apenas empréstimos
      contratados têm performance), default rate crescente por vintage
- [x] Prototipado em memória no 1.0 (o 1.1 produtiza, não re-deriva): casts de dtype no load
      (`DATA`/`REFERENCIA` → datetime, `SAFRA` → int, `risco_aposta` → categorical)
      e o join por data da aplicação (`REFERENCIA` = `DATA`, left join simples — os snapshots
      são disparados pela aplicação; verificado equivalente a uma regra asof point-in-time)
- [x] **1.1 Construir a tabela interim de aplicações**: reaplicar casts de dtype, sentinelas → NaN
      (`score_klavi_1` -999999, `status_empregaticio` '-999999'), manter `Capacidade Financeira`
      negativa como válida (apenas sinalizar os extremos), left join em `uuid` +
      data da aplicação (`REFERENCIA` = `DATA`) para uma linha por aplicação (todos os STATUS),
      flags de coverage/segmento, unicidade da chave assertada, escrito em `data/interim/`
- [x] **1.2 Multiplicidade & grain**: investigadas as repetições intra-mês (mesmo `uuid`, mesmo
      `SAFRA`, datas distintas) — sem `contract_id`/valor para provar equivalência, e `Contratado`
      mostra 88 grupos de contratos distintos (todos em datas diferentes, 7 com `OVER30M2`
      divergente). Deduplicar por prioridade de STATUS recuperaria ~0 snapshot (a disponibilidade
      segue o `uuid`, não a linha). **Decisão: manter o grain `(uuid, DATA)`** (1.1 inalterado); a
      sobre-representação por usuário em IV/WoE vira decisão de ponderação na Fase 2.

## Fase 2 — Análise de variáveis (relevância e representatividade)

A fase avança **variável a variável** seguindo os pontos 2→6 da Abordagem, sobre a amostra
rotulada `Contratado` — o **caveat de viés de seleção vale para todo número aqui**. A
distribuição (ponto 1) já foi coberta em 1.0 §6; a passagem da variável para a política (pontos
7–8) é a Fase 3. O trabalho se divide entre **2.0 — binning workbench** (estima, persiste e
ajusta à mão os bins), **2.1 — univariate signal** (coverage, ranking IV, shortlist) e **2.2 —
shortlist validation** (redundância, estabilidade, leakage, ponderação); a máquina WoE/IV vem do
módulo `src/credit_policy/` (`woe.py`, `binning.py`), os bins de `references/bin_spec.yaml` e o
shortlist de `credit_policy.VAR_SELECTION` — fontes únicas de verdade para 2.0/2.1/2.2 e notebooks
seguintes.

**2. Coverage (representatividade)** — *2.1 §1*
- [x] Contagem non-missing + % da amostra rotulada por variável; três camadas: flags 100%,
      amplas ~46–52% (`score_klavi_2`, `Capacidade Financeira`, categóricas), trio open-finance
      ~4,5% (`score_klavi_1`, `Renda`, `risco_aposta`).
- [x] Missing como **segmento explícito**, não só NaN: bin `(missing)` em toda variável + flags
      `has_snapshot` / `has_open_finance` como variáveis binárias — isola "a disponibilidade em
      si é preditiva?".
- [x] Cobertura simétrica entre STATUS (1.0 §3 / O Problema) → o viés está no label, não na
      disponibilidade; a cobertura é representativa da população through-the-door.

**3. Relação com o target — IV / WoE** — *módulo `credit_policy.woe`; demo 2.1 §2; perfis 2.0 §4*
- [x] Máquina WoE/IV (`WoE = ln(%goods/%bads)`, positivo = mais seguro; suavização 0,5); IV
      sobre bins ocupados, incluindo `(missing)` — agora em `src/credit_policy/woe.py`.
- [x] Bad rate e WoE por bin; perfis de forma do risco ("WoE geral", 2.0 §4).

**4. Binning** — *2.0 (binning workbench)*
- [x] Estimativa inicial por quantis (`estimate_spec`: `n_bins = clip(n_nonmiss//200, 2, 10)`,
      cortes internos; categóricas: 1 grupo/categoria, raras (<2%) → `(outros)`), **persistida em
      `references/bin_spec.yaml`** (esquema de cut-points, editável à mão).
- [x] **Ordenação / monotonicidade + estabilidade** (Abordagem ponto 4): bins fundidos à mão no
      `bin_spec.yaml` via WoE geral (2.0 §5) + WoE por safra (2.0 §6), com tabela WoE por bin em
      2.0 §4 — `classe_social` → A/B/C vs D/E; `status_empregaticio` → `Desempregado` dobrado em
      `Desconhecido`; `Capacidade Financeira` e `score_klavi_2` recortados para menos bins,
      monótonos e estáveis.

**5. Relevância — IV** — *ranking/shortlist 2.1 §2; estabilidade WoE 2.0 §6; PSI/IV 2.2 §3*
- [x] Ranking IV = discriminação × coverage (2.1 §2): sinal modesto em toda a linha (nenhuma
      variável ≥ 0,1; nada em território de leakage > 0,5). `classe_social` 0,091 lidera; trio
      open-finance ≈ 0 por causa dos 95,5% de missing.
- [x] Shortlist `VAR_SELECTION` (congelada em `credit_policy.VAR_SELECTION`): `classe_social`,
      `Capacidade Financeira`, `score_klavi_2`, `status_empregaticio`. **`regiao` (próxima por IV,
      0,025) excluída por fairness** — região é proxy de atributos protegidos (risco de redlining /
      disparate impact); o teste de disparate impact fica para a Fase 3 (precisa do scorecard).
- [x] Estabilidade do sinal (visual): WoE por bin ao longo de SAFRA (2.0 §6) —
      `classe_social` a mais estável; separação de `score_klavi_2` comprime a partir de 202503.
- [x] **PSI** por variável ao longo de SAFRA e **IV por vintage** (2.2 §3): três estáveis
      (PSI < 0,03); `score_klavi_2` com PSI 0,32 numa safra e IV volátil (0,01–0,18) → mantida com
      flag **"watch"** (revisitar bins/recência na Fase 3).

**6. Redundância** — *2.2 §2*
- [x] Correlação pós-binning (WoE) entre as candidatas, com correção de co-missingness (matriz
      *overlap-only* vs *naive*): todos os pares |r| < 0,4 (máx. `classe_social` × `Capacidade
      Financeira` 0,39) → **sem redundância, mantém as quatro**. Bloco socioeconômico
      (`classe_social`, `status_empregaticio`) + bloco financeiro (`Capacidade Financeira`,
      `score_klavi_2`), complementares.

**Transversal**
- [x] **Triagem de leakage** (2.2 §4): nada perto de leakage (todos IV < 0,1, |WoE| < 1);
      features são snapshots Klavi na data da aplicação (point-in-time por construção) → passa.
- [x] **Sensibilidade de ponderação** (2.2 §5, herdado do 1.2): um-registro-por-`uuid` derruba só
      849 de 24.148 linhas; IV muda < 0,001 e o ranking não se altera → shortlist robusto.

**Saída da fase**: shortlist final validado — `classe_social`, `Capacidade Financeira`,
`score_klavi_2` (watch), `status_empregaticio` — com forma, estabilidade, redundância, leakage e
ponderação resolvidos; `regiao` excluída por fairness. Alimenta a Fase 3.

## Fase 3 — Proposta de política (regras + score)

**Desenho**: **segmento** = `classe_social` × `status_empregaticio` (2 × 3 + `(missing)`), com um
**cutoff de `score_klavi_2` por segmento**. `Capacidade Financeira` fica fora do v1 (candidata a 2º
eixo depois). Swap-set assimétrico: maus removíveis do book são medidos (`Contratado`); bons
alcançáveis no estoque não-contratado são inferidos.

**Variável `segmento` (habilitador — YAML/módulo paralelos; reusa binning + máquina do 2.0)**
- [x] Novo `references/segment_spec.yaml` (paralelo ao `bin_spec.yaml`) p/ segmentações por
      composição de variáveis — extensível a outros segmentos. Entrada única:
      `segmento: {dims: [classe_social, status_empregaticio], groups: ...}`.
- [x] Novo módulo `credit_policy/segments.py` (paralelo a `binning.py`): `make_segments(binned, spec)`
      cruza as **dims já binadas** numa coluna de células (`A/B/C · Formal`, …); `(missing)` em
      qualquer dim → `(missing)`; fusão de células via `groups:` **reusando o `apply_spec`
      categórico** (identidade p/ células não listadas). Reusa `load_spec`.
- [x] `binning.py` **inalterado**: um segmento cruzado é só mais uma categórica → WoE/PSI/over-time
      o recebem sem mudança.

**3.0 — Mapa de segmentos & estoque** — *notebook 3.0*
- [x] População por `segmento` × STATUS + coverage de `score_klavi_2` por célula: **`(missing)` é
      48,6% do funil e 49% do book**; coverage de score ~89–90% nas células nomeadas vs 1,1% no
      `(missing)` (score e demografia co-missing) → cutoff por segmento é bem-posto exatamente nas
      células nomeadas; o `(missing)` **é** o caminho sem-score.
- [x] Em `Contratado`, por segmento: três tiers de risco — A/B/C 6,5–7,8%, `(missing)` 11,5%,
      D/E 15,5–16,4% (2,4×; WoE +0,50 → −0,54).
- [x] Visual do swap-set: estoque concentra onde o risco é menor (A/B/C: 31,6k `Aprovado` + 41,4k
      `Reprovado`; `(missing)`: 95,3k). **A política atual desordena**: `A/B/C · Formal` (célula
      mais segura, 6,5%) tem approval 43,7% < `A/B/C · Desconhecido` (50,1% com 7,8%).
- [x] Colapso de células finas: `D/E · Formal` (22 rotuladas / 356 no total) fundida em
      `D/E · Autônomo/Formal` via `groups:` do `segment_spec.yaml`.
- [x] Segmentação fundida **persistida em `data/processed/applications_segmented.parquet`**
      (tabela de aplicações + coluna `segmento`; categórica ordenada sobrevive ao round-trip) —
      3.1+ consomem a coluna em vez de re-derivar.

**3.1 — Risco por segmento & WoE do score** (reusa 2.0; input = tabela processada do 3.0) — *notebook 3.1*
- [x] Baseline por segmento: ordenação A/B/C > `(missing)` > D/E **persiste em 74/78 células
      segmento×safra** (flips todos |WoE| ≤ 0,11, small-n); mix de segmentos com PSI ≤ 0,027 —
      a estrutura demográfica é a parte estável da política (vs `score_klavi_2` PSI 0,32 no 2.2).
- [x] Score dentro de cada segmento: **ordena o risco de ponta a ponta nas 5 células nomeadas**
      (ex.: `D/E · Autônomo/Formal` 21,4%→6,1%, gradiente 3,5× — cutoff por segmento > negar a
      célula inteira); monotonicidade estrita oscila no meio em 2 células (ruído de bin fino;
      3.2 varre cutoff contínuo). `(missing)` sem eixo de score utilizável (113 rotuladas).
- [x] Regra do score ausente, explícita: sem-score **dentro de célula nomeada** defaulta ao
      baseline do segmento (Δ −2,3 a +1,9 pp vs com-score, sem sinal consistente — não é seleção
      adversa); segmento `(missing)` = célula própria a 11,5% (decisão de apetite no 3.2 +
      alavanca de aquisição de dados via consentimento snapshot/open-finance).

**3.2 — Simulação de cutoffs & trade-off** — *notebook 3.2; política em `references/policy_v1.yaml` + `credit_policy/policy.py`*
- [x] Cutoff contínuo por segmento nomeado (menu de conjuntos aninhados `score ≥ c`); família de
      políticas parametrizada por uma tolerância de risco **τ** (aprova toda unidade com default
      medido ≤ τ).
- [x] **`(missing)` fora do sweep de τ, por desenho** — sem score nem demografia, não há o que
      cortar. Em vez de aprovar tudo (extrapolação com zero variável observada) ou negar tudo, a
      regra é `mode: keep_current`: **preserva a decisão já tomada pelo cliente** (aprova
      `STATUS ∈ {Aprovado, Contratado}`, nega `Reprovado`) — assume-se que existe um processo do
      cliente fora das nossas 4 variáveis, mantido em vigor. Como todo o book rotulado
      `(missing)` é `Contratado`, o bloco vira um **piso fixo** (49% do book, 11,5% descritivo,
      não decisório) presente em qualquer τ — o "penhasco" da versão anterior desaparece.
- [x] Curva de trade-off: **não-monotônica** — cai antes de subir (τ baixo dilui o piso de 11,5%
      com fatias mínimas e seguras dos nomeados; τ maior traz volume maior e mais arriscado,
      inclusive D/E, puxando de volta para 10,3%). Alavanca por `classe_social` emerge dos dados:
      A/B/C sem gate de score; D/E com cutoffs reais (≥ 595 / ≥ 518) e sem-score negado.
- [x] Ponto de operação recomendado: **τ\\* = 11,5%** (nos nomeados) → mantém 90% do book a
      **9,64% vs 10,30%** (o que sai defaulta a 16,3%); persistido em `references/policy_v1.yaml`,
      aplicado por `credit_policy.policy.approve` (fonte única p/ 3.3+).
- [x] Cenário de extrapolação **sinalizado e agora delimitado**: nos segmentos nomeados (única
      hipótese real, apoiada em segmento+score), as regras admitiriam **36,1% do `Reprovado`**
      (43,1k de 119,2k) a ~7,4% assumido, e 42,2% do `Aprovado` nomeado (32,6k) — expansão só via
      teste estagiado e monitorado. No `(missing)`, **nenhuma hipótese é pedida**: os 57,8k
      `Reprovado` seguem negados (status quo do cliente), e os 37,5k `Aprovado` seguem aprovados
      sem reavaliação — nem extrapolação nem negação nova, apenas preservação.

**3.3 — Fairness / disparate impact** (adiado da Fase 2) — *notebook 3.3*
- [x] Approval por `regiao` (atual vs `policy_v1` simulada, população com região ~52%): **sem
      impacto díspar residual** — four-fifths passa e *melhora* (0,832 → 0,931); diferenças
      remanescentes acompanham o risco medido por região (Nordeste 11,2% vs Sul 6,2%), não a
      região em si. Reavaliar com aprovações realizadas quando a política/teste entrar em vigor.

**Saída da fase**: política v1 completa e justificável — segmentação persistida (3.0), baseline e
eixo de score validados + regra do sem-score (3.1), fronteira de trade-off com ponto de operação
em `policy_v1.yaml` e o bloco `(missing)` deferido ao status quo do cliente (3.2), checagem de
fairness aprovada (3.3). Expansão ao estoque `Reprovado` permanece hipótese a testar de forma
estagiada, restrita aos segmentos nomeados onde há evidência; `(missing)` não é objeto de
hipótese — conversão em células nomeadas (mais dados) é a maior alavanca estrutural futura.
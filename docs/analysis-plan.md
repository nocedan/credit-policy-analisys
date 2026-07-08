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
5. **Relevância** — definida pelo IV (discriminação + coverage) e pelo papel da variável (se
   atua dentro das aplicações aprovadas ou das negadas).
6. **Redundância** — correlação pós-binning entre candidatas, para não repetir sinal na proposta final.

**Da variável à política**

7. **Nova política** — estruturar a concessão a partir da discriminação das variáveis dentro e
   fora das aprovadas.
   - Boa discriminação dentro das aprovadas + boa cobertura nas negadas → oportunidade de
     ampliar a concessão.
   - Ainda assim, a abertura deve ser conservadora: de 202501 em diante o default rate cresce
     com inclinação consistente.
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

## Fase 2 — Análise de variáveis (relevância e representatividade)

- [ ] **2.0 Sinal univariado**: IV / WoE por variável (binned), default rate por decil,
      gráficos de separação (KDE/ROC por variável)
- [ ] Estratégia de missing-data: tratar "sem dados Klavi" (47,7%) e "sem consentimento
      open-finance" (91,3% para score_klavi_1/Renda/risco_aposta) como segmentos explícitos,
      não apenas NaN
- [ ] **Estabilidade**: PSI de cada variável ao longo de SAFRA; estabilidade do sinal (IV por vintage)
- [ ] Correlação / redundância entre candidatas (ex.: score_klavi_2 × Capacidade Financeira)
- [ ] Triagem de leakage: qualquer variável suspeitosamente preditiva → questionar sua
      disponibilidade point-in-time

## Fase 3 — Proposta de política (regras + score)

- [ ] **3.0 Desenho da política candidata**: regras simples e explicáveis (cutoffs em
      variáveis de ampla coverage) + ranking baseado em score para a faixa intermediária
- [ ] Análise de swap-set vs. política atual (mudanças de aprovação/recusa e seu impacto
      esperado no default)
- [ ] Curva de trade-off approval rate × default rate esperados para o time de negócio
      escolher o ponto de operação

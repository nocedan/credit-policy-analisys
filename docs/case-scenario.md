# Case Scenario - Credit Granting Policy Review

**Introduction**:
 You are working as a Senior Data Scientist at a Klavi a firm specialized in credit risk. A Fintech Client wants to review their credit granting policy and needs to define: 
 
- Which variables are most relevant for predicting default 
 
- Which variables are good candidates for a practical credit policy (rules + score) 
 
- How to turn these variables into an objective and justifiable proposal for the business team

**Challenge**: You are given one week to analyze the data files provided by the client. You must deliver a recommendation on how to proceed using Klavi’s variables. Using a visual approach, show how to analyze the data and extract meaningful business insights.

**Please detail**: 
 
- The main steps you would take to explore, clean, and organize the provided dataset.
- The key factors or criteria you would consider essential to ensure the insights are relevant, accurate, and representative.
- How you would validate both the analytical approach and the insights generated.

---

## Respostas — variáveis relevantes e candidatas à política

As duas primeiras perguntas do caso já estão respondidas pela Fase 2 (ver
[analysis-plan.md](analysis-plan.md)). **São perguntas distintas**, e os dados divergem
exatamente onde importa. Todos os números abaixo vêm da amostra rotulada `Contratado` — a única
com target (`OVER30M2`) observável.

**Q1 — quais variáveis são mais relevantes para prever default** (ranking IV, notebook 2.1 §2):
sinal modesto em toda a linha (nenhuma variável ≥ 0,1; nada em território de leakage).
`classe_social` lidera (IV 0,091); o trio open-finance (`score_klavi_1`, `Renda`, `risco_aposta`)
fica ≈ 0 **por causa** dos 95,5% de missing — não por fraqueza intrínseca da variável.

**Q2 — quais variáveis são boas candidatas a uma política prática (regras + score)** (shortlist
validado): `classe_social`, `Capacidade Financeira`, `score_klavi_2` (flag *watch*) e
`status_empregaticio` — aprovadas em coverage, redundância, estabilidade/PSI, leakage e
ponderação.

**Q1 ≠ Q2**, e a diferença é ela própria um achado:

- `regiao` — 2ª por IV (0,025), logo *tem* relevância (Q1), mas **não** é candidata (Q2):
  excluída por fairness (proxy de atributos protegidos / risco de redlining).
- trio open-finance — falha Q1 **apenas por coverage**, não por mérito da variável.

**Caveat central.** `Aprovado` e `Reprovado` **não têm target** — não há como observar se uma
variável discrimina *dentro* desses grupos. Como extrapolar com segurança a discriminação medida
nas `Contratadas` para os demais STATUS é uma **questão da Fase 3**, não algo mensurável agora.
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

## Respostas — variáveis, política e proposta (análise concluída)

**Por que agora.** A inadimplência (`OVER30M2`) subiu de ~8–10% (safras de 2024) para 12,5%
(jun/2025) enquanto o approval rate caiu de ~54% para ~40%: a régua foi apertada e, ainda assim, o
default piorou. O problema não é *aprovar menos* — é *aprovar melhor*.

**Como ler os números.** Tudo que é *medido* vem da amostra rotulada — os 24.148 `Contratados`
(10,3% de default), a única com performance observável. `Aprovado`/`Reprovado` não têm target; a
proposta trata esse ponto de frente (item Q3, "expansão com segurança").

**Q1 — Quais variáveis são mais relevantes para prever default?**
*Não há bala de prata.* Nenhuma variável isolada discrimina fortemente — `classe_social` lidera,
mas modestamente, seguida de perto por `Capacidade Financeira`, `score_klavi_2` e
`status_empregaticio`. O trio open-finance (`score_klavi_1`, `Renda`, `risco_aposta`) é inutilizável
não por fraqueza, mas porque **falta em 95,5% dos pedidos**. *Implicação:* a política precisa
**combinar variáveis complementares**, não depender de um único score. (Ranking IV: `classe_social`
0,091 > `Capacidade Financeira` 0,067 > `score_klavi_2` 0,037 > `status_empregaticio` 0,031 >
`regiao` 0,025.)

**Q2 — Quais são boas candidatas a uma política prática (regras + score)?**
Quatro variáveis, todas validadas (não-redundantes, estáveis no tempo, sem leakage, robustas a
reaplicações): **`classe_social`, `Capacidade Financeira`, `score_klavi_2` e `status_empregaticio`**.
Duas ressalvas que são, elas próprias, decisões: `score_klavi_2` entra **sob observação** (menos
estável no tempo); `regiao`, embora relevante (Q1), é **excluída por fairness** — proxy de atributos
protegidos, risco de redlining.

**Q3 — Como transformar isso numa proposta objetiva e justificável para o negócio?**
Uma política de **dois níveis**, simples de explicar e auditar:

1. **Segmentar** pelo bloco socioeconômico estável — `classe_social` × `status_empregaticio`. É a
   parte *estável* do risco (a ordenação A/B/C > D/E se sustenta em 74 de 78 janelas mensais).
2. **Cortar por score** dentro de cada segmento (`score_klavi_2`). O score ordena o risco de ponta a
   ponta *dentro* de cada célula (no D/E mais arriscado, o corte separa 21% de 6% de default) — mais
   preciso e mais justo do que negar uma célula inteira. *(A v1 usa um único eixo de score,
   transparente; `Capacidade Financeira` — a 4ª candidata — fica reservada como 2º eixo numa v2.)*

- **Impacto (medido no book):** ao **mesmo nível de aprovação (~90%)**, o default cai de **10,3% para
  9,64%**; a fatia recusada inadimple a 16,3%. A política corrige distorções da régua atual — hoje a
  célula mais segura (`A/B/C·Formal`, 6,5%) é aprovada *menos* que células mais arriscadas.
- **Onde a Klavi agrega, refina; onde não, respeita o processo do cliente:** em ~metade do funil a
  Klavi não recebe snapshot. Isso **não** significa decisão sem informação — a concessão ali segue o
  **processo próprio do cliente** (seus dados e score), que a Klavi simplesmente não observa. A régua
  proposta **não se sobrepõe** a esse processo: mantém a decisão atual nesse bloco e concentra o
  refinamento onde a Klavi de fato adiciona sinal. Ampliar a cobertura Klavi (consentimento
  snapshot/open-finance) **estende o alcance** da nova régua a esse bloco — a maior alavanca
  estrutural de médio prazo.
- **Justiça e governança:** `regiao` fica **fora** da régua como variável — evita proxy de atributos
  protegidos (risco de redlining); e toda a política vive num spec versionado e editável à mão,
  auditável ponto a ponto.
- **Expansão com segurança (o viés de seleção, resolvido em desenho):** performance só existe nos
  contratados, então abrir a concessão aos hoje reprovados é *hipótese*, não medição. A recomendação
  **adota os cortes já no fluxo corrente** (efeito medido) e trata a expansão como **teste estagiado
  e monitorado** — que, de quebra, gera os rótulos que hoje faltam.
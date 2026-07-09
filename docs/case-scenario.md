# Cenário do Caso — Revisão da Política de Concessão de Crédito

**Introdução**:
 Você trabalha como Cientista de Dados Sênior na Klavi, uma empresa especializada em risco de crédito. Um Cliente Fintech quer revisar sua política de concessão de crédito e precisa definir: 
 
- Quais variáveis são mais relevantes para prever default 
 
- Quais variáveis são boas candidatas para uma política de crédito prática (regras + score) 
 
- Como transformar essas variáveis em uma proposta objetiva e justificável para o time de negócio

**Desafio**: Você tem uma semana para analisar os arquivos de dados fornecidos pelo cliente. Você deve entregar uma recomendação de como proceder usando as variáveis da Klavi. Com uma abordagem visual, mostre como analisar os dados e extrair insights de negócio significativos.

**Detalhe**: 
 
- Os principais passos que você tomaria para explorar, limpar e organizar o conjunto de dados fornecido.
- Os fatores ou critérios essenciais que você consideraria para garantir que os insights sejam relevantes, acurados e representativos.
- Como você validaria tanto a abordagem analítica quanto os insights gerados.

---

## Respostas — variáveis, política e proposta (análise concluída)

**Por que agora.** A inadimplência (`OVER30M2`) subiu de ~8–10% (safras de 2024) para 12,5%
(jun/2025) enquanto o approval rate caiu de ~54% para ~40%: a régua foi apertada e, ainda assim, o
default piorou. O processo atual responde ao cenário de forma a *aprovar menos* -- Nossa proposta seria *aprovar melhor*.

**Como ler os números.** Tudo que é *medido* vem da amostra rotulada — os 24.148 `Contratados`
(10,3% de default), a única com performance observável; a
proposta trata esse ponto de frente (item Q3, "expansão com segurança").

**Q1 — Quais variáveis são mais relevantes para prever default?**
Nenhuma variável isolada discrimina fortemente — `classe_social` lidera, seguida de perto por `Capacidade Financeira`, `score_klavi_2` e
`status_empregaticio`. O trio "open-finance" (`score_klavi_1`, `Renda`, `risco_aposta`) é inutilizável mas porque é **missing em 95,5% dos pedidos**. *Implicação:* a política precisa
**combinar variáveis complementares**, não depender de um único score. (Ranking IV: `classe_social`
0,091 > `Capacidade Financeira` 0,067 > `score_klavi_2` 0,037 > `status_empregaticio` 0,031 >
`regiao` 0,025.)

**Q2 — Quais são boas candidatas a uma política prática (regras + score)?**
Quatro variáveis, todas validadas (não-redundantes, estáveis no tempo, sem leakage, robustas a
reaplicações): **`classe_social`, `score_klavi_2` e `status_empregaticio`**.
Duas ressalvas que são, `regiao`, embora relevante (Q1), é **excluída por fairness** — proxy de atributos
protegidos; e Capacidade financeira, que possui valores negativos -- algo a ser validado e entendido.

**Q3 — Como transformar isso numa proposta objetiva e justificável para o negócio?**
Uma possível proposta, seria uma política de **dois níveis**, simples de explicar e auditar:

1. **Segmentar** pelo bloco socioeconômico estável — `classe_social` × `status_empregaticio`. É a
   parte *estável* nas safras observadas.
2. **Cortar por score** dentro de cada segmento (`score_klavi_2`). O score ordena o risco de ponta a
   ponta *dentro* de cada célula (no D/E mais arriscado, o corte separa 21% de 6% de default) — mais
   preciso e mais justo do que negar uma célula inteira.

- **Impacto (medido no book):** ao **mesmo nível de aprovação (~90%)**, o default cai de **10,3% para
  9,64%**; a fatia recusada inadimple a 16,3%. A política corrige distorções da régua atual — hoje a
  célula mais segura (`A/B/C·Formal`, 6,5%) é aprovada *menos* que células mais arriscadas.
- **Onde a Klavi agrega, refina; onde não, respeita o processo do cliente:** em ~metade do funil a
  Klavi não recebe snapshot. Isso **não** significa decisão sem informação — a concessão ali segue o
  **processo próprio do cliente** (seus dados e score), que a Klavi simplesmente não observa. A régua
  proposta **não se sobrepõe** a esse processo: mantém a decisão atual nesse bloco e concentra o
  refinamento onde a Klavi de fato adiciona sinal.
- **Expansão com segurança (o viés de seleção, resolvido em desenho):** performance só existe nos
  contratados, então abrir a concessão aos hoje reprovados é *hipótese*, não medição. A recomendação
  **adota os cortes já no fluxo corrente** (efeito medido) e trata a expansão como **teste estagiado
  e monitorado** — que, de quebra, gera os rótulos que hoje faltam.

---

## Respostas — método (explorar, garantir qualidade, validar)

**1. Explorar, limpar e organizar.**
Uma linha por aplicação no "grain" `uuid` + data (`(uuid, DATA)`), unindo performance e features pela
data da decisão. Limpeza *conservadora*: só sentinelas
comprovados (`-999999`) viram `NaN`; missing tratado como **categoria explícita**, não descartado.
Camadas para organização dos dados raw → interim → processed, com as decisões (binning de features, segmentação, política) persistidas em
documentos versionados versionados e editáveis — com o pipeline reproduzível ponta a ponta.

**2. Critérios para insight relevante, acurado e representativo.**
- **Representatividade:** medir só onde há target (`Contratado`) e explicitar o **viés de seleção** — estimativas nos contratados são apenas hipóteses a serem confirmadas para as transação sem contratação.
- **Cobertura antes de sinal: utilizar o Information Value com o WoE** uma variável forte com 5% de cobertura não sustenta política; IV pesa
  discriminação **e** disponibilidade.
- **Estabilidade no tempo:** só entra o que se mantém safra a safra (PSI, WoE por cohort).
- **Fairness:** excluir proxies de atributos protegidos (`regiao`) por desenho, não só por
  performance.

**3. Validar abordagem e insights.**
- **Estabilidade:** ordenação de risco consistente ao longo das safras (não um artefato de um mês).
- **Impacto contrafactual:** swap-set e curva approval × default no book (carteira) rotulada — ganho *medido*,
  não prometido.
- **Rollout:** cortes primeiro no fluxo corrente (efeito observável), expansão só via **teste
  estagiado** que gera os rótulos que hoje faltam.
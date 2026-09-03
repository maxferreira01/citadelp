# Domínio — vocabulário e estruturas reais (das planilhas)

Fonte: 2 planilhas operacionais anexadas (21/07/2026). Nomes de pessoas anonimizados nos mocks.

## Datacenters (Edges) reais
TECE01 · TESP02 · TESP03 · TESP04 · TESP05 · TESP06 · TESP07 · TBSP01 · TBSP02 (+ TESP04 Projeção IaaS)
Estados de DC usados na operação: **Produção · Recebendo Migrações · Vegetativo · Contingência**

## Recursos monitorados (nomes reais)
- Firewall Físico — Memória (%) · limite 85
- Firewall Físico — Data Plane CPU (%) · limite 85
- NSX IP Set / Objetos IPSET · limites 9.200–30.000
- NSX — Logical Switch Port · limites 24.000–36.000
- NSX — NAT Rules · limites 24.500–25.000
- NSX T1 (por T0-Cluster_1..4 + vrf_1/vrf_2) · **200 T1s por cluster** (ex. real: 200/200 usados!)
- Link Internet Output (Gbps) · ex.: 1,71/2,0 · 838/2000
- L2L entre sites (ex.: TESP3↔TBSP2 — IPN1) · 3.910/10.000
- ACI — MAC_PER-IP por cluster
- IPs públicos por cluster: Total 254/316 (blocos /24), Utilizados, Livres, IPs por cliente
- Consolidado: Clientes, IPs, NATs, Internet (Mbps), VMs, Hosts físicos, Storage usado (TB) / provisionado (PB), Backup (TB/objetos), CPU (GHz), RAM (TB), Ativações/mês

## Estruturas de tabela reais (calibram colunas dos componentes)
**Dashboard de capacidade (por DC):** `# (rank) | Recurso | Limite | Uso atual | Média cresc. 12m | Cresc. mês atual | Tempo de vida (dias) | Data | Percentual`
**Controle de recursos / plano de ação (por Edge):** `Edge | Quem trouxe | Status (Em aberto/Em andamento) | Criticidade (Critical/Warning) | Data | Recurso | Uso atual | Limite | Ação sugerida | Responsável`
**Painel por DC:** Visão IPs públicos · Visão NSX (T1s por cluster) · Visão NATs por FW · Visão ACI
**Crescimento consolidado:** Crescimento mês atual | Média/dia | Estimado mês — por Clientes/IPs/NATs/NSX/ACI
**Financeiro:** abas Baseline_OR-2025, ORC X REA (orçado × realizado), Projeção ORC, Import_FinOpps, Import_Eletrica/HV/Storage/Backup, RMI

## Problemas de qualidade observados (justificam o princípio 7)
- "Tempo de vida (dias)" com valores negativos/absurdos (-1200, -634980, 410387) — fórmula quebrada quando crescimento ≤ 0 → o DS precisa do estado **"previsão impossível/degradada"**
- Percentuais como 0,887826087 sem arredondamento; datas como serial Excel — formatação inconsistente
- 77 abas mensais (Dezembro2k21…Maio2k26) + 33 abas por DC/ano: histórico fragmentado à mão
- Colunas "Responsável: A definir", células vazias, "TESTE" em nome de aba

## Ações sugeridas típicas (tom de voz real da equipe)
"Upgrade para 3Gbps ou balanceamento" · "Transbordar migrações para o T…" · "Edge em estado vegetativo — limite…" · "Upgrade de banda — devido a…"

## Implicações para o design system
1. Runway/saturação é a métrica-mãe (tempo de vida em dias já existe, mas quebra — a Cidadela corrige com estado de confiança).
2. Recursos têm nomes longos (30+ chars) → coluna Recurso precisa de largura generosa + truncamento com tooltip.
3. Hierarquia DC → cluster (T0) → vrf → recurso é real: tabela hierárquica é componente central.
4. Limites variam por DC para o mesmo recurso → limite é atributo do par (DC, recurso).
5. Financeiro (ORC×REA) convive com capacidade no mesmo arquivo → integração Tesouro⇄Três Olhos é orgânica.

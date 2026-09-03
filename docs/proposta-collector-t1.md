# Proposta — nsx-collector: capacity de T1 (redigida em 25/08/2026, NÃO executada)

Origem: `docs/validacao-nsx-t1-25-08.md`. Fluxo de sempre: commit no repo
`coletores/nsx-collector`, deploy box a box (git pull + rebuild + restart +
`systemctl enable`). Referências de linha são da leitura de 24/08 — confirmar
com grep antes de editar.

## 1. `nsx_t1_totals` no bucket errado (V1 confirmada)

Hoje: `capacity.go:191` empurra o ponto para o slice default → `worker.go:285`
→ bucket `nsx`. Os 6 painéis de total do `dashboards/Capacity-NSX/dashboard.json`
(linhas 127, 175, 285, 342, 2511) leem `nsx_capacity` e ficam em branco.

**Direção proposta: mover o ponto para `nsx_capacity`** (junto de per_t0,
per_vrf e nsx_capacity, que é onde um leitor procura), e não reescrever os
painéis. Motivos: (a) é 1 linha no Go × 6 edições no JSON; (b) deixa
`nsx_capacity` autocontido para retenção própria; (c) o citadel já isola a
escolha em `Consultas.b_totals` — trocar para `bucket_capacity` no mesmo PR.

Custo: o histórico de `nsx_t1_totals` desde 11/06 fica no bucket `nsx` (não
migrar; o citadel pode ler os dois buckets com `union()` por 90 dias se o
`Trajectory` precisar do passado — ou aceitar o corte).

Patch (esboço):
```go
// internal/collector/capacity.go ~:191
- points = append(points, influxdb.T1TotalsPoint(site, totals))
+ capacityPoints = append(capacityPoints, influxdb.T1TotalsPoint(site, totals))
```
(usar o slice que `worker.go` roteia via `writer.go:44-58` para `nsx_capacity`.)

## 2. Novo measurement `nsx_t1_per_edge_cluster` (maior valor / menor esforço)

O join T1 → edge cluster já é calculado a cada ciclo (`capacity.go:159-164`) e
só vai para eventos e para `state/t1watch-<site>.json`. Hoje o "edge por edge"
só sai via `scripts/nsx_t1capacity.py --com-edge`, que pagina 1854
logical-routers na Manager a cada execução — ruim como rotina.

```
measurement: nsx_t1_per_edge_cluster   bucket: nsx_capacity
tags:   site, edge_cluster_name, edge_cluster_id
fields: t1_count (int)        # opcional: limit/usage_pct se houver premissa por EC
```
Molde: `points.go:729-759` (`nsx_t1_per_t0`). Contagem de referência no TESP6
em 25/08: EC-Cluster_1 607, EC-Cluster_2 597, EC-Cluster_3 601, EC-Cluster_4 36,
sem EC 1 (T1 sem SR — contar como `edge_cluster_name="-"`).

Com isso o citadel ganha rota `/nsx/t1/por-edge` e o gráfico "por edge" no
Três Olhos sem tocar na Manager.

## 3. Tag `site` — normalização

Presente já está limpo (V2): nenhuma box escreve `TESP06/TESP07` desde
~02/07/2026. Só o histórico de `nsx_t1_event` de junho carrega as variantes.
Ação: nenhuma no collector; manter `CITADEL_NSX_SITE_ALIASES` no citadel e,
se algum `managers.yaml` ainda tiver `site: "TESP0X"`, corrigir no próximo
deploy daquela box (conferir box a box no molde do V3).

## 4. `parent_kind` como tag de `nsx_t1_event`

`nsx_t1_event.vrf_name` recebe `ParentT0Name` (`capacity.go:239`) — é nome de
VRF ou de T0 conforme o caso (TESP7 e o T0-Cluster_4 do TESP6 penduram T1
direto no T0). O snapshot já tem `parent_kind` (`state.go:18-27`).
Expor como tag `parent_kind=t0|vrf` no ponto (`points.go:886-919`) e, no mesmo
PR, renomear/duplicar `vrf_name` → `parent_name` (manter `vrf_name` por
compatibilidade com o t1-slack-bot até ele ser ajustado). O citadel já expõe
o campo como `parent_name` em `EventoT1`.

## 4b. `t0_parent` de VRF fora do padrão de nome

`capacity.go:181` deduz o T0 pai da VRF pelo sufixo `-vrf_` no display name.
VRFs como `T0-Cluster_1_FG3`, `T0-Cluster_1_PA2` (TECE) e
`T0-Cluster_1-Tenant_Shared-1` (TESP6/TECE) saem com `t0_parent = "-"`, e o
T1 por par de edges fica subcontado (TECE Cluster_1: 211 gravados × 546 reais).
Usar o campo da API — `vrf_config.tier0_path` do gateway VRF
(`/policy/api/v1/infra/tier-0s`) — e cair na heurística só se ele faltar. O
citadel infere pelo prefixo do nome enquanto isso (`consultas._pai`, marcado
`parent_inferido`), confirmado no TECE pelo `nsx_ha_state`.

## 5. Colaterais observados (não são bugs do collector)

- 6 de 8 VRFs do TESP6 a ≥ 99,5 % de `vrf_t1_limit_default: 200`. Se 200/VRF é
  regra de arquitetura, `t1_watch.enabled` deveria estar ligado no TESP6 (hoje
  `false`) — decisão do time, não deste runbook.
- Janela 16–18/06/2026 sem garantia de eventos (collector instável); 1 T1
  (`TEZOUX_C8PV75_ate`) sem `created`. O snapshot cobre.
- Evento sintético `t1-cliente-novo`/`teste-blockkit-1` (11/06, site TESP06)
  ainda está no bucket `nsx` — filtrar por `t1_id != "teste-blockkit-1"` em
  quem contar eventos, ou apagar via `delete` API se incomodar.

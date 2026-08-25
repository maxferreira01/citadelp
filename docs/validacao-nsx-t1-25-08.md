# Validação — capacity de T1 NSX · dev-redes TESP6 · 25/08/2026

Executada conforme `docs/runbook-nsx-t1-capacity.md` (§3), tudo somente leitura:
Flux no InfluxDB central (10.114.35.75:8086, org TOTVS) e GET no NSX Manager do
TESP6 (10.114.36.200). Sem token/senha aqui.

Box: `dev-redes` (TESP6). `nsx-collector` ativo desde 26/06/2026 11:53, binário em
`/home/nsx_collector/`, config em `configs/config.yaml` + `configs/managers.yaml`,
estado em `state/t1watch-tesp6.json` (1842 T1 conhecidos, atualizado 15:38).

## V1 — bucket do `nsx_t1_totals` (dívida a) — **CONFIRMADA**

| bucket | `nsx_t1_totals` (últimas 2 h) |
|---|---|
| `nsx` | 8 sites × 3 fields (total/on_vrf/on_t0) |
| `nsx_capacity` | **vazio** |

Veredito: o collector grava no bucket default (`nsx`); os painéis de total do
Grafana (`dashboards/Capacity-NSX/dashboard.json`) que consultam `nsx_capacity`
estão em branco. O citadel lê de `nsx` (`backend/app/nsx/consultas.py`,
`Consultas.b_totals`). Direção proposta em `docs/proposta-collector-t1.md` §1.

Totais por site (last, 25/08 ~18:40 UTC):

| site | total | on_t0 | on_vrf |
|---|---|---|---|
| TECE | 1025 | 312 | 713 |
| TESP2 | 2347 | 1601 | 746 |
| TESP3 | 2277 | 890 | 1387 |
| TESP4 | 661 | 460 | 201 |
| TESP5 | 2243 | 815 | 1428 |
| TESP6 | 1842 | 635 | 1207 |
| TESP7 | 1703 | 600 | 1103 |
| TESP7-INFRABASE | 2 | 2 | 0 |

Parque: **12.100 T1** (soma dos 8 sites). `nsx_capacity/NUMBER_OF_TIER1_ROUTERS`
bate com `total` em todos os sites (`max_supported` = 4000, exceto
TESP7-INFRABASE = 400).

## V2 — variantes da tag `site` (dívida b) — **resolvida no presente, viva no histórico**

`schema.tagValues` (janela default de 30 d) nos dois buckets: `TECE, TESP2, TESP3,
TESP4, TESP5, TESP6, TESP7, TESP7-INFRABASE` — nenhuma variante com zero.

Mas `first()` em 365 d de `nsx_t1_event` mostra as antigas:

| site tag | primeiro evento |
|---|---|
| TESP06 | 2026-06-11 23:53 (evento sintético `t1-cliente-novo` / `teste-blockkit-1`) |
| TESP07 | 2026-06-11 22:02 |
| TESP6 | 2026-07-02 19:36 |
| TESP7 | 2026-06-12 13:07 |

→ `CITADEL_NSX_SITE_ALIASES='{"TESP06":"TESP6","TESP07":"TESP7"}'`. Retenção do
bucket `nsx` começa em 11/06/2026 (primeiro ponto de `nsx_t1_totals` TESP6).
`TESP7-INFRABASE` é um site legítimo (Manager separado), não variante.

## V3 — config do collector nesta box (dívida c)

`/home/nsx_collector/configs/config.yaml` (mtime 26/06/2026):

```yaml
intervals: { default: 40s, traffic: 15s, slow: 5m, ha: 1m }
t1_watch:
  enabled: false            # baseline validado, alerta segue desligado
  vrf_t1_limit_default: 200
  t0_t1_limit_default: 1000
  vrf_t1_limits: {}  t0_t1_limits: {}
capacity:
  track_t1_events: true
  collect_segments: true  collect_gw_policies: true  collect_groups: true
  collect_nat_per_t1: false  nat_per_t1_pace_ms: 30  nat_per_t1_parallel: 4
```

Ou seja: bloco `capacity:`/`t1_watch:` presente e explícito nesta box (não é só
default do Go). As outras boxes precisam da mesma conferência, box a box.

## V4 — Manager TESP6 × Influx — **BATE**

| fonte | T1 |
|---|---|
| `GET /policy/api/v1/infra/tier-1s?page_size=1` → `result_count` | **1842** |
| `GET /api/v1/capacity/usage` → `NUMBER_OF_TIER1_ROUTERS.current_usage_count` | 1842 / 4000 (46,05 %, INFO) |
| Influx `nsx_t1_totals.total` (bucket `nsx`) | 1842 (on_t0 635 + on_vrf 1207) |
| Influx Σ `nsx_t1_per_t0.t1_count` | 635 |
| Influx Σ `nsx_t1_per_vrf.t1_count` | 1207 |
| Influx `nsx_capacity.current_usage` | 1842 |
| snapshot `t1watch-tesp6.json` `.known` | 1842 |
| Manager `logical-routers` TIER1 por edge cluster | 607 + 597 + 601 + 36 + 1 (sem EC) = 1842 |

Zero eventos `nsx_t1_event` nas 2 h anteriores — sem movimento na janela.
Reproduzível com `scripts/nsx_t1capacity.py --site TESP6 --validar --com-edge`
(rodado 15:53 BRT, `validacao.ok = true`).

Por T0 / VRF (TESP6):

| T0 | T1 | limite | % |
|---|---|---|---|
| T0-Cluster_1 | 203 | 1000 | 20,3 |
| T0-Cluster_2 | 198 | 1000 | 19,8 |
| T0-Cluster_3 | 200 | 1000 | 20,0 |
| T0-Cluster_4 | 34 | 1000 | 3,4 |

| VRF | parent | T1 | limite | % |
|---|---|---|---|---|
| T0-Cluster_1-vrf_1 | T0-Cluster_1 | 202 | 200 | **101,0** |
| T0-Cluster_3-vrf_2 | T0-Cluster_3 | 201 | 200 | **100,5** |
| T0-Cluster_2-vrf_1 | T0-Cluster_2 | 200 | 200 | **100,0** |
| T0-Cluster_3-vrf_1 | T0-Cluster_3 | 200 | 200 | **100,0** |
| T0-Cluster_1-vrf_2 | T0-Cluster_1 | 199 | 200 | 99,5 |
| T0-Cluster_2-vrf_2 | T0-Cluster_2 | 199 | 200 | 99,5 |
| T0-Cluster_1-Tenant_Shared-1 | – | 4 | 200 | 2,0 |
| T0-Cluster_4-vrf_1 | T0-Cluster_4 | 2 | 200 | 1,0 |

**Achado colateral:** 6 das 8 VRFs do TESP6 estão no limite de 200 T1/VRF. Esse
200 é `vrf_t1_limit_default` da config do collector (premissa operacional, não
config-max da VMware) — todo crescimento novo está indo para T0-Cluster_4
(todos os 7 `created` desde julho). Vale confirmar se 200/VRF é regra de
arquitetura (aí a Muralha deveria mostrar isso) ou só default do collector.

## V5 — creation time × eventos × snapshot

API (`_create_time`) lista **8 T1 criados após o baseline** (11/06/2026 23:41):

| T1 | `_create_time` (UTC) | `nsx_t1_event` created | `first_seen` snapshot |
|---|---|---|---|
| TFDHH9_CD942K_ate | 21/08 14:48 | 21/08 14:49 ✓ | 21/08 14:49 ✓ |
| TEZIUT_CUAGJY_ate | 19/08 13:47 | 19/08 13:48 ✓ | ✓ |
| TFBLFX_C74VMO_ate | 07/08 18:02 | 07/08 18:05 ✓ | ✓ |
| TESP6-CloudPulse | 16/07 23:55 | 16/07 23:55 ✓ | ✓ |
| T07123_C97AGD_ate | 15/07 18:17 | 15/07 18:17 ✓ | ✓ |
| tks-td29f29 | 10/07 15:30 | 10/07 15:35 ✓ | ✓ |
| T56141_CGJFY5_ate | 07/07 17:14 | 07/07 17:15 ✓ | ✓ |
| TEZOUX_C8PV75_ate | **17/06 13:47** | **sem evento** | 17/06 13:48 ✓ |

Deleted: `TSALVA4_CSALVA4_ate` 02/07 19:36 (evento ✓; não está mais na API ✓).

O único buraco é `TEZOUX_C8PV75_ate` (17/06): o snapshot viu (first_seen 1 min
depois da criação) mas o evento não foi gravado. A contagem diária de pontos de
`nsx_t1_totals` mostra a janela: 16/06 = 165 pts, **17/06 = 96**, 18/06 = 43
(normal ≈ 270/dia) — collector instável/reiniciando nesses dias (época dos
deploys de capacity), e a tag ainda oscilava TESP06/TESP6. Não é para
"consertar": registrar a janela **16–18/06/2026** como sem garantia de eventos.
Além disso, 19/08 teve 178 pts (breve parada, sem T1 perdido).

Latência criação→evento: 1–5 min, coerente com o ciclo `slow = 5m`.

## Gate

V4 bateu → implementação seguiu (`backend/app/nsx`, `scripts/nsx_t1capacity.py`,
frontend). Propostas de collector em `docs/proposta-collector-t1.md`.

## Notas de execução

- O `.env` do collector guarda a senha entre aspas simples; ao ler com `grep`
  cru a aspa vai junto e o Manager devolve **403 "credentials incorrect or
  locked"** — foram 2 tentativas erradas antes de perceber. Usar `set -a; .
  ./.env` (ou strip das aspas). Ficou como cuidado no `carregar_env()` do CLI.
- Já existe um uvicorn antigo na porta 5533 desta box (pid 2737403, código
  anterior a este módulo) — para o Vite proxy ver `/nsx/*`, reiniciá-lo.

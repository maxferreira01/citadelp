# Runbook — Capacity de T1 NSX no Citadel: validar, implementar, commitar

> Executado em 25/08/2026 na dev-redes do TESP6 — resultados em
> `docs/validacao-nsx-t1-25-08.md`; propostas de collector em
> `docs/proposta-collector-t1.md`. O que segue é o roteiro, para repetir em
> outra box/site.

**Para rodar numa dev-redes com rota para o InfluxDB central (10.114.35.75:8086)
e para o NSX Manager do site.** Autocontido: dá para colar num Claude Code na
box e executar do topo ao fim.

Escopo em três blocos, nesta ordem:

1. **Validar** as três dívidas de dados + conferir o número de T1 direto na
   Manager contra o Influx e contra os creation times.
2. **Implementar/atualizar** o módulo `nsx` no citadelp (read-model sobre o
   Influx + CLI de snapshot/validação + frontend) e **commitar**.
3. **Propor** (por escrito, sem executar) as mudanças que são do nsx-collector.

## Trilhos (não negociáveis)

- **NSX Manager: somente GET.** Nenhum POST/PUT/PATCH/DELETE em equipamento.
- **Não mexer no serviço `nsx-collector` da box** — sem restart, sem editar
  config. Só leitura dos arquivos.
- Se um GET autenticado devolver **401/403, PARE naquele alvo** — não repita
  (lockout de conta). Atenção: o `.env` do collector guarda valores entre
  aspas simples; `grep` cru manda a aspa junto e produz 403 falso. Use
  `set -a; . ./.env; set +a`.
- Nunca commitar `.env`, token de Influx ou senha. `relatorios/` está no
  `.gitignore`.

## 1. Contexto — o que já existe

### 1.1 O nsx-collector já coleta capacity de T1

Coletor Go, 1 instância por site nas dev-redes (systemd, `Restart=always`),
todos escrevendo no **InfluxDB central `http://10.114.35.75:8086`, org
`TOTVS`**, buckets `nsx` (default) e `nsx_capacity`. Ciclo de capacity =
`intervals.slow` = **5 min**.

| measurement | bucket | tags | fields |
|---|---|---|---|
| `nsx_t1_totals` | **`nsx`** (confirmado V1) | `site` | `total`, `on_vrf`, `on_t0` |
| `nsx_t1_per_t0` | `nsx_capacity` | `site`, `t0_name`, `t0_id` | `t1_count`, `limit`, `usage_pct`, `available` |
| `nsx_t1_per_vrf` | `nsx_capacity` | `site`, `vrf_name`, `vrf_id`, `t0_parent` | idem |
| `nsx_capacity` | `nsx_capacity` | `site`, `usage_type`, `display_name` | `current_usage`, `max_supported`, `usage_pct` |
| `nsx_t1_event` | `nsx` | `site`, `event`, `t1_id`, `t1_name`, `vrf_name`*, `edge_cluster_name` | `count`, `vrf_t1_count`, `vrf_limit`, `site_t1_total` |

\* `vrf_name` no evento é o **nome do parent (VRF ou T0)**.

**Não existe no Influx:** T1 por edge cluster como série (proposta §5.2). O
join está no snapshot `state/t1watch-<site>.json` (com `first_seen`).

### 1.2 As três dívidas

- **(a)** `nsx_t1_totals` no bucket `nsx`, painéis Grafana consultam
  `nsx_capacity` → painéis de total em branco. **Confirmada em 25/08.**
- **(b)** Tag `site` inconsistente (TESP06/TESP6, TESP07/TESP7) — hoje limpa,
  histórico de jun/2026 ainda carrega. Mapa em `CITADEL_NSX_SITE_ALIASES`.
- **(c)** Config drift por site: conferir `capacity:`/`t1_watch:` box a box.

### 1.3 Onde está no citadelp

`backend/app/nsx/` (config, client Flux, consultas, modelos, artefatos,
manager GET-only, router), `scripts/nsx_t1capacity.py`, testes em
`backend/tests/test_nsx_*.py`, frontend `useNsxT1()`/`T1Bars` em
`frontend/src/CitadelApp.jsx`.

## 2. Setup na box

```bash
git clone git@github.com:maxferreira01/citadelp.git && cd citadelp
python3.12 -m venv .venv && .venv/bin/pip install -e "backend[dev]"
.venv/bin/pytest backend -q
systemctl cat nsx-collector      # -config, -managers, -env-file
```

Helper Flux:

```bash
INFLUX=http://10.114.35.75:8086
TOKEN=$(grep -oP '(?<=^INFLUX_TOKEN=).*' /home/nsx_collector/.env | tr -d "'\"")
flux() { curl -s "$INFLUX/api/v2/query?org=TOTVS" -H "Authorization: Token $TOKEN" \
  -H 'Content-Type: application/vnd.flux' -H 'Accept: application/csv' --data-binary @-; }
```

## 3. Validações (somente leitura)

### V1 — bucket do `nsx_t1_totals`
```bash
for b in nsx nsx_capacity; do echo "== $b"; flux <<EOF
from(bucket: "$b") |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "nsx_t1_totals")
  |> last() |> keep(columns: ["site","_field","_value"])
EOF
done
```

### V2 — variantes da tag `site`
`schema.tagValues` olha só 30 d; para o histórico use `first()` em 365 d
agrupado por `site` em `nsx_t1_event` e `nsx_t1_totals`.

### V3 — config do collector
```bash
grep -n -A12 -E '^(capacity|t1_watch|intervals):' /home/nsx_collector/configs/config.yaml
```

### V4 — Manager × Influx
```bash
set -a; . /home/nsx_collector/.env; set +a
MGR=https://<url do managers.yaml>
curl -sk -u "$NSX_TESPX_USER:$NSX_TESPX_PASS" "$MGR/policy/api/v1/infra/tier-1s?page_size=1" | jq .result_count
curl -sk -u "$NSX_TESPX_USER:$NSX_TESPX_PASS" "$MGR/api/v1/capacity/usage" \
  | jq '.capacity_usage[] | select(.usage_type=="NUMBER_OF_TIER1_ROUTERS")'
```
No Influx: `nsx_t1_totals` (bucket `nsx`), Σ `t1_count` de per_t0 + per_vrf,
`nsx_capacity.current_usage`. **Critério:** tudo igual ao `result_count`,
tolerando eventos `created/deleted` na janela de 15 min. Nota Flux: `last()`
+ `pivot` exige `toFloat()` antes (fields long × double).

Automatizado: `scripts/nsx_t1capacity.py --site TESPX --validar --com-edge`
(exit = nº de sites divergentes).

### V5 — creation time × eventos × snapshot
```bash
# API: _create_time (paginar por cursor, page_size=1000)
# eventos: nsx_t1_event created em -90d
# snapshot: jq '.known | to_entries[] | [.value.name, (.value.first_seen|todate), .value.parent_kind, .value.parent_t0_name, .value.edge_cluster_name] | @tsv' state/t1watch-<site>.json
```
Todo T1 com `_create_time` posterior ao baseline deve ter `created`; buraco =
janela de collector parado — anotar, não consertar.

**Gate:** V4 batendo → implementar. Divergindo além da janela → parar e
reportar (tshoot no collector).

## 4. Implementação no citadelp

Branch `nsx-t1-capacity`, commits por etapa (backend → CLI → frontend → docs).

### 4.1 `.env` (nunca commitar; `.env.example` tem os placeholders)
`CITADEL_INFLUX`, `CITADEL_INFLUX_TOKEN` (ideal: token read-only próprio),
`CITADEL_NSX_SITE_ALIASES`, `CITADEL_NSX_MANAGERS` + `NSX_<SITE>_USER/PASS`.

### 4.2 Backend — rotas somente leitura
`GET /nsx/t1/resumo[?site=]`, `/por-t0?site=`, `/por-vrf?site=`,
`/historico?site=&dias=`, `/eventos?site=&dias=`, `/snapshot?site=`.

### 4.3 CLI — `scripts/nsx_t1capacity.py`
`--site X|todos`, `--probe`, `--validar`, `--com-edge`, `--criacao`. Snapshot em
`relatorios/nsx-t1capacity/<SITE>/`. É a "query diária": agendável em cron
na box ou k8s CronJob (molde `deploy/k8s/corvo-cronjob.yaml`).

**Edge produtivo (TESP7):** o crescimento/mês da aba de previsão vem do
`_create_time` de cada T1 na Manager (`--criacao` → `criacao-<ts>.json`;
rota `/nsx/t1/crescimento?site=TESP7`), não do Influx — o bucket só retém
desde jun/2026 e o site nasceu em mai/2025. Rodar diariamente; a diferença
entre snapshots revela remoções. Os demais sites usam o collector.
Cron sugerido na dev-redes do TESP6 (alcança a Manager do TESP7):
`15 6 * * * cd /root/citadelp && .venv/bin/python scripts/nsx_t1capacity.py --site TESP7 --criacao >> relatorios/nsx-t1capacity/cron.log 2>&1`

### 4.4 Frontend
Três Olhos (`useNsxT1`, `T1Bars`) e Muralha leem `/nsx/t1/*`; chip OBS.
Proxy do Vite → `localhost:5533`; `make run` sobe na 8000 — alinhar ao rodar.

### 4.5 Fechamento
`pytest backend -q` verde, `ruff check backend scripts/nsx_t1capacity.py`
limpo, `npm run build` ok, docs de validação sem segredos.

## 5. Propostas para o nsx-collector
Ver `docs/proposta-collector-t1.md` (bucket de totals, `nsx_t1_per_edge_cluster`,
tag `site`, `parent_kind` no evento).

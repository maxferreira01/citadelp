# Runbook — Mapa de portas ACI + validação de cobertura no Checkmk

**Para rodar numa dev-redes** (ou qualquer box com rota para os APICs e para os
sites Checkmk). Tudo até o passo 4 é **somente leitura** (GETs no APIC e no
Checkmk). Escrita no Checkmk só existe no passo 5, atrás de `--apply`.

O que isto faz: mapeia toda porta física de leaf dos fabrics ACI, classifica
(uplink de fabric/APIC, NSX edge, firewall, roteador, SW99, acesso a servidor,
livre, desconhecida), valida **leaf a leaf se o Checkmk está monitorando**, e
gera as regras que desligam NOTIFICAÇÃO das portas de acesso — a coleta
continua (os gráficos de CRC no Grafana dependem dela). Alarme fica só em
uplink de infraestrutura.

---

## 1. Setup na box (uma vez)

Dev-redes é RHEL. O código exige **Python ≥ 3.11** (RHEL 9: appstream tem):

```bash
sudo dnf install -y python3.11 git
git clone git@github.com:maxferreira01/citadelp.git   # ou https com token
cd citadelp
python3.11 -m venv .venv
.venv/bin/pip install -e "backend[dev]"
.venv/bin/pytest backend -q        # sanidade: 50 passed
```

## 2. `.env` na raiz do repo (nunca commitar; `chmod 600 .env`)

Os oito fabrics. **SENHA-COMUM** = a senha admin dos APICs que você já usa
(a mesma do survey de portas livres). **Exceção: TESP7 usa essa mesma senha
repetida duas vezes, sem separador** (confirmado em 24/08/2026).

```bash
CITADEL_ACI_FABRICS='[
 {"id":"TESP2","apic_url":"https://172.18.251.14","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tesp2"},
 {"id":"TESP03","apic_url":"https://10.100.35.14","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tesp3"},
 {"id":"TESP04","apic_url":"https://10.103.35.14","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tesp4"},
 {"id":"TESP05","apic_url":"https://10.108.35.14","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tesp5"},
 {"id":"TESP6","apic_url":"https://10.114.35.100","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tesp6"},
 {"id":"TESP7","apic_url":"https://10.118.35.14","user":"admin","secret":"SENHA-COMUM-2X","verify_tls":false,"cmk_site":"tesp7"},
 {"id":"TECE01","apic_url":"https://172.18.252.14","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tece1"},
 {"id":"TBSP02","apic_url":"https://10.102.10.14","user":"admin","secret":"SENHA-COMUM","verify_tls":false,"cmk_site":"tbsp2"}
]'
```

> O JSON precisa ficar **numa linha só** no `.env` (o exemplo acima está
> quebrado só para leitura).

E os sites Checkmk — **automation user com role mínima, um por site** (para a
cobertura basta leitura; a URL é `https://host/site`, sem `/check_mk`). O `id`
tem que bater com o `cmk_site` do fabric acima:

```bash
CITADEL_CHECKMK_SITES='[
 {"id":"tesp2","url":"https://cmk-infra-01.tesp2infra.local/mk_tesp2","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tesp3","url":"https://tesp3cmk1p00001.tesp3infra.local/mk_tesp3","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tesp4","url":"https://tesp4cmk1p00001.tesp4infra.local/mk_tesp4","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tesp5","url":"https://tesp5cmk1p00001.tesp5infra.local/mk_tesp5","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tesp6","url":"https://tesp6cmk1p00001.tesp6infra.local/mk_tesp6","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tesp7","url":"https://10.118.16.11/mk_tesp7","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tece1","url":"https://cmk-infra-tece1-01.tece1infra.local/mk_tece1","user":"USUARIO","secret":"SEGREDO"},
 {"id":"tbsp2","url":"https://tbsp2cmk1p00001.tbsp2.local/mk_tbsp2","user":"USUARIO","secret":"SEGREDO"}
]'
```

> URLs vieram do inventário de IPs de gerência (TDN pág. 10). Atenção à
> divergência conhecida: **tece1 e tesp2 apontam para o mesmo IP
> (172.18.162.11)** — a validação acusa a colisão se for real.

## 3. Mapa de portas (GET no APIC) — `scripts/aci_portmap.py`

```bash
.venv/bin/python scripts/aci_portmap.py --fabric todos --probe   # 1 login por APIC, só testa
.venv/bin/python scripts/aci_portmap.py --fabric todos           # mapa completo (~2-15 min/fabric)
```

- **Se um probe der 401, PARE nele** — não repita a tentativa (lockout AAA).
  O script já se comporta assim sozinho.
- Do laptop (24/08) já foram mapeados TESP2/03/04/05/6/7 = **146 leafs**;
  daqui o objetivo principal é **TECE01 e TBSP02** (inalcançáveis de lá).
  Se preferir não re-coletar os outros 6, copie a pasta
  `relatorios/aci-portmap/` do laptop — os CLIs usam sempre o mapa mais
  recente de cada fabric.
- Artefatos por fabric em `relatorios/aci-portmap/<FABRIC>/`
  (`portmap-*.csv` para revisar, `.json` para os próximos estágios,
  `resumo-*.csv` leaf×classe). Nada disso vai para o git.

## 4. **Validação de cobertura** (GET no Checkmk) — `scripts/aci_cobertura.py`

A pergunta "todo leaf está monitorado?", respondida leaf a leaf:

```bash
.venv/bin/python scripts/aci_cobertura.py                 # todos os fabrics com mapa
.venv/bin/python scripts/aci_cobertura.py --fabric TESP6  # um só
```

O que sai (tela + `relatorios/aci-portmap/cobertura-<ts>.csv`):

| Situação | Significado / ação |
|---|---|
| `monitorado ... [exato]` | leaf ACI tem host homônimo no site esperado — ok |
| `monitorado ... [normalizado]` | nomes divergem só em zeros (ex. `LEAF1017TESP07`↔`TESP7`) — ok, mas vale padronizar |
| `monitorado ... [numero-unico]` | casou só pelo número do leaf (ex. leafs `TBSP2` dentro do fabric TESP2) — **revisar** |
| `NAO-MONITORADO` | leaf existe no ACI e **não tem host no Checkmk** → criar a monitoração |
| `COLISÃO: host também em [...]` | mesmo host respondendo por mais de um site (caso tece1/tesp2) — **resolver antes de qualquer regra** |
| `orfao-no-cmk` | host `LEAF*` no Checkmk sem leaf no mapa ACI (descomissionado?) |
| `site X: SEM REST (1.5)` | site legado — validar pela GUI; regras desse site sairão como `.md` manual |

Exit code 1 se houver leaf não monitorado (dá para usar em script/CI).

Para criar a monitoração de leaf faltante, o citadelp já tem o caminho
pronto: `POST /checkmk/{site}/hosts` (cria host + discovery + activate) — ou
pela GUI, como preferir.

## 5. (Depois, com o mapa revisado) Silenciamento — `scripts/aci_silenciar.py`

Só depois de revisar os CSVs (em especial as **desconhecidas**, que continuam
alarmando de propósito):

```bash
.venv/bin/python scripts/aci_silenciar.py --fabric TESP6              # dry-run: plano-regras-<ts>.json + divergencias, ZERO escrita
.venv/bin/python scripts/aci_silenciar.py --fabric TESP6 --apply      # efetiva NAQUELE site (remove regras CITADEL antigas → cria → activate)
.venv/bin/python scripts/aci_silenciar.py --fabric TESP6 --verificar  # os dois lados: alvo silenciado E uplink ainda notificando
```

Trilhos de segurança embutidos (não dependem de disciplina do operador):

- só silencia porta classificada **acesso_servidor/livre**; desconhecida e
  vizinho LLDP não reconhecido **nunca** entram;
- só leafs casados com confiança **alta** entram em regra;
- `--apply` recusa `todos` — rollout é site a site, com revisão entre eles;
- regras idempotentes (`CITADEL aci-portmap <FABRIC> gNN <data>` no ruleset
  `extra_service_conf:notifications_enabled`): reaplicar substitui, nunca
  acumula; todos os padrões de serviço têm âncora `$`;
- recomendação: aplicar primeiro no TESP6 (piloto validado), conferir o
  dashboard de CRC no Grafana e uns dias de plantão antes dos demais.

## 6. Estado em 24/08/2026 e pendências

- Mapeados do laptop: TESP2 (30 leafs), TESP03 (26), TESP04 (6), TESP05 (22),
  TESP6 (30), TESP7 (32) — 146 leafs, ~7.800 portas. Gate do piloto TESP6:
  60/60 uplinks conferidos contra o CSV do aci-lldp-collector.
- **Pendente nesta box**: mapa de TECE01 e TBSP02; cobertura de todos.
- 94 portas **desconhecidas** aguardando revisão humana
  (`relatorios/aci-portmap/revisao-desconhecidas-*.csv` no laptop): UCS FI
  (`tesp5ucs*`), appliances `PEGASUS`/`athena`, NICs Broadcom sem identidade.
  Elas seguem alarmando até alguém decidir.
- NSX edges e firewalls não anunciam LLDP para o leaf — a classificação deles
  vem da `descr` das portas; manter as descrições em dia é o que sustenta o
  mapa.

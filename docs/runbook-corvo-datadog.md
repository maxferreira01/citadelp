# Runbook — Corvo · Datadog (relatório diário do #datadog-redes + bot de consulta)

**O que é.** Um app Slack ("Corvo") que acompanha o canal privado `#datadog-redes`
(`C087SV98MBM`, bot Datadog `U07Q4UQU0GM`) e:

1. manda todo dia às **08:00 BRT** uma **DM** para o Bruno (`CORVO_REPORT_TO`) com o
   resumo da janela **08:00 D-1 → 08:00 D** (Block Kit) e o **PDF** completo na thread;
2. responde **comandos** na DM (só usuários de `CORVO_BOT_ALLOWED_USERS`);
3. fica **sempre ligado** (Socket Mode) gravando as transições das pages — é assim que o
   tempo de **ack** fica exato (o Datadog edita a mensagem *in place*; o histórico do
   Slack só guarda o estado final).

Tudo no Slack é **somente leitura** exceto: postar na DM e subir o PDF.

## Comandos da DM

| Escreva | Resposta |
|---|---|
| `hoje` · `ontem` · `7d` · `30d` | resumo do período (+ PDF) |
| `plantão` (ou `quem`) | quem está de plantão Interna/Externa (último *Handover Summary*) + responders desde 08:00 |
| `mês` | chamados no mês vs mês anterior, por tipo/time/DC |
| `tempo médio [7d\|30d\|mês]` | resposta humana, ack (exato/proxy), primeiro toque, resolução |
| `top dc [período]` | ranking de datacenters |
| `recorrentes [período]` | (servidor, evento) e INCs repetidos |
| `sem resposta [período]` | pages sem resposta/reação/ack |
| `alerta 52488` · `alerta INC13450` · `alerta 21714051` | card da page (timeline, quem falou, recorrência) |
| `tesp3` · `tece1 7d` · `tbsp2 mês` | resumo de **um datacenter**: pages, sem resposta, ack, status, responders, eventos mais frequentes |
| `reenviar pdf` | último PDF gerado |
| `ajuda` | lista + botões |

Período padrão das consultas: 30 dias. Os botões do relatório disparam os mesmos comandos.

**Botões por datacenter.** A `ajuda` e o relatório diário trazem uma linha com um botão por
DC (`TESP2 … TESP7 · TECE1 · TBSP1 · TBSP2 · TBSP3 · TBCE1`, lista fixa em `bot.py::DC_BUTTONS`;
um DC fora da lista que apareça na janela ganha botão também). No relatório o botão mostra a
contagem da janela (`TESP3 (5)`) e consulta **o mesmo período** do relatório; na ajuda consulta
30 dias. A resposta do DC tem botões `Hoje · Ontem · 7d · 30d` do próprio DC e a linha de DCs
de novo, para pular de site em site.

## Métricas (o que cada número significa)

- **t0** = hora em que o Datadog postou a page no Slack.
- **Resposta humana** = 1ª mensagem de gente (não bot) ligada à page: reply na thread
  → mensagem no canal citando `#page`, servidor ou INC → mensagem no canal em até 30 min
  atribuída à page mais recente ainda sem resposta.
- **Ack (Datadog)** = transição para *Acknowledged* − t0. Fonte: `live` (evento ao vivo,
  exato) > `edited_ts` (última edição da mensagem, exato enquanto a page ainda está
  Acknowledged) > `proxy` (page já Resolved sem evento ao vivo: usa a resposta humana).
  O relatório sempre mostra a fonte; com o bot no ar o `live` domina em poucos dias.
- **Sem resposta** = nenhuma resposta, reação nem *Responder*. **Ack silencioso** =
  alguém assumiu no Datadog e ninguém falou no Slack.
- **Recorrência** = mesma dupla (servidor, evento) na janela / 7d / 30d; INCs contados à parte
  (`21714051` do Cherwell ≠ `INC13450` do ServiceNow — não se misturam).
- **DC** = extraído do hostname (`LEAF1001TESP03`→TESP03, `tesp3cmk1p00004-floating`→TESP03,
  `monitoring-redes-1-tece01`→TECE01). Fora da família conhecida vira `?` e aparece em
  "sem DC reconhecido" — nunca é descartado.

## 1. Criar o app Slack (uma vez)

1. <https://api.slack.com/apps> → **Create New App → From a manifest** → cole
   `deploy/slack-app-manifest-corvo.yml`.
2. **Basic Information → App-Level Tokens → Generate** com escopo `connections:write`
   → `SLACK_APP_TOKEN` (`xapp-…`).
3. **Install to Workspace** → *Bot User OAuth Token* → `SLACK_BOT_TOKEN` (`xoxb-…`).
4. No `#datadog-redes`: `/invite @Corvo` (canal privado: sem convite dá `not_in_channel`
   e nenhum evento chega).
5. Bruno precisa abrir a DM com o app uma vez (ou o bot abre via `conversations.open` no
   primeiro envio — o `im:write` cobre isso).

## 2. Setup na dev-redes (RHEL 9)

```bash
git clone git@github.com:maxferreira01/citadelp.git /opt/citadelp   # ou o clone que já existe
cd /opt/citadelp
sudo bash deploy/systemd/install.sh            # deps (python3.11, pango), venv, units, .env
sudo vi .env                                   # SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CORVO_REPORT_TO
sudo bash deploy/systemd/install.sh            # re-rode: sobe o bot quando os tokens existem
```

O `install.sh` cria o usuário de sistema `citadel` (ou `CORVO_USER=...`), deixa o repo,
`data/` e `relatorios/` com esse dono, `.env` em 0600 e instala:

- `corvo-datadog-bot.service` — sempre ligado (`Restart=always`);
- `corvo-datadog-report.timer` → `corvo-datadog-report.service` (08:00 BRT, `Persistent=true`:
  se a box estava desligada, roda ao voltar).

Saída de rede necessária: `https://slack.com` e `wss://wss-primary.slack.com` (Socket Mode).

## 3. Primeiro dia

```bash
cd /opt/citadelp
# 1) popular 30 dias (recorrência) sem postar, guardando o raw pra conferir o parser
sudo -u citadel .venv/bin/python collectors/corvo_datadog_report.py --dry-run --scan-days 30 --dump-raw
#    → confira "mensagens do bot não parseadas" = 0; raw em relatorios/corvo-datadog/<data>/raw.json
# 2) mandar só pra você
sudo -u citadel .venv/bin/python collectors/corvo_datadog_report.py --send --to U053RFRVBE1
# 3) na DM do Corvo: ajuda · plantão · mês · tempo médio 7d · alerta <page de hoje>
# 4) quando estiver bom: CORVO_REPORT_TO=U3BBS1RA6 no .env e deixa o timer trabalhar
```

## 4. Operação

```bash
systemctl status corvo-datadog-bot            # bot no ar?
journalctl -u corvo-datadog-bot -f            # eventos: "canal: transition:Triggered->Acknowledged"
systemctl list-timers 'corvo-datadog-*'       # próximo disparo do relatório
systemctl start corvo-datadog-report          # reenviar agora (respeita CORVO_REPORT_TO)
sqlite3 data/corvo_datadog.sqlite "select status,source,count(*) from transitions group by 1,2"
```

Atualizar código: `git pull && sudo bash deploy/systemd/install.sh` (reinicia o bot; o
timer não é afetado). Artefatos em `relatorios/corvo-datadog/<AAAA-MM-DD>/` (gitignored):
`*.html`, `*.pdf`, `*.json` (mesmo layout do JSON do float-ip, para o raio-x do frontend).

Opções úteis do job: `--date 2026-08-27` (fim da janela), `--days 7` (semanal), `--offline`
(sem ler o Slack), `--no-pdf`, `--skip-replies`.

## 5. Problemas conhecidos

| Sintoma | Causa / ação |
|---|---|
| `not_in_channel` no scan ou bot mudo no canal | bot não convidado no `#datadog-redes` |
| `weasyprint não importa` no install | falta `pango` na box — o job segue anexando HTML; `dnf install pango dejavu-sans-fonts` |
| ack sempre `proxy` | bot não estava no ar quando a page foi reconhecida (normal nos primeiros dias / após reboot longo) |
| "mensagens do bot não parseadas" > 0 | Datadog mudou o template — abra o `raw.json`, ajuste `backend/app/corvo/datadog.py` e os fixtures em `backend/tests/test_datadog_parse.py` |
| DM não chega | `CORVO_REPORT_TO` errado, ou app sem `im:write`; teste com `--send --to <seu U>` |
| Socket Mode cai/reconecta | normal; `Restart=always` cobre; sem rede para `wss-primary.slack.com` o bot fica em loop de reconexão |

## Onde está cada coisa

- Parser puro: `backend/app/corvo/datadog.py` · testes `backend/tests/test_datadog_parse.py`
- Store SQLite: `backend/app/corvo/datadog_store.py` · métricas `datadog_metrics.py` ·
  agregações `datadog_query.py` (QueryEngine — única fonte de números)
- Scan do histórico: `datadog_scan.py` · eventos ao vivo: `bot_app.py::apply_event`
- Comandos: `bot.py` (puro) · relatório: `datadog_report.py` + `templates/`
- Entrypoints: `collectors/corvo_datadog_report.py`, `collectors/corvo_datadog_bot.py`
- Deploy: `deploy/systemd/` · manifesto do app: `deploy/slack-app-manifest-corvo.yml`
- API de apoio: `POST /corvo/parse-datadog` (valida o parser contra uma mensagem crua)

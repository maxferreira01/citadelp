# HANDOFF — Corvo · Datadog na dev-redes (bot + relatório diário do #datadog-redes)

> Abra este arquivo no Claude Code da dev-redes e siga na ordem. Ele contém o
> contexto inteiro: o que já foi feito no laptop, o que executar aqui, como
> validar e o que NÃO fazer. Detalhes de operação: `docs/runbook-corvo-datadog.md`.

## Missão

Colocar em produção, nesta box, o app Slack **Corvo** (já criado, já instalado no
workspace, já convidado no `#datadog-redes`), que:

1. fica **sempre ligado** (Socket Mode) gravando ack/resolve das pages do Datadog
   ao vivo — sem isso o tempo de ack sai "aproximado";
2. manda **08:00 BRT** o relatório do plantão (resumo Block Kit + PDF) por **DM**
   para `CORVO_REPORT_TO`;
3. responde comandos na DM (`plantão`, `mês`, `tempo médio`, `top dc`, `alerta <id>`…).

Fonte: canal `#datadog-redes` (`C087SV98MBM`), bot Datadog `U07Q4UQU0GM`. Toda
leitura do Slack é somente leitura; o app só escreve na DM dos destinatários.

## Regras invioláveis

1. **Segredo só no `.env`** (0600, dono do serviço). Nunca em argv, log, commit
   ou chat. Os tokens do app **já circularam em chat uma vez** — depois que
   isto estiver estável, rotacione-os em api.slack.com (Reinstall → novo xoxb;
   App-Level Tokens → regenerate xapp) e atualize o `.env`.
2. **Nada de `pip install` fora do venv do repo.** O `install.sh` cuida disso.
3. `data/` e `relatorios/` ficam na box (gitignored) — contêm nomes de gente e
   hosts de cliente.
4. Não mexer no `#datadog-redes`: o bot não posta lá, só lê.

## Estado atual (o que já foi feito no laptop, 28/08/2026)

- Código no repo `citadelp` (módulo Corvo): parser, store SQLite, métricas,
  QueryEngine, scan, relatório HTML/PDF, bot slack_bolt, CLI, units systemd,
  `install.sh`, manifesto do app, runbook. **92 testes passando** (`make lint && make test`).
- App Slack **Corvo** (`A0BT7JSGYP5`, bot user `U0BTFPCEV7B`) criado pelo
  manifesto `deploy/slack-app-manifest-corvo.yml`, instalado, convidado no canal.
- Scan real de 30 dias validado: 608 pages, 50 handovers, **zero mensagens sem
  parse**. Relatório já enviado e revisado na DM do Max; Bruno e Wendell já
  usaram os comandos na DM.
- O laptop do Max rodou o bot durante o dia 28/08 — o SQLite de lá tem
  transições `live` desse dia. **Não é necessário copiar**: o 1º scan aqui
  repopula 30 dias (só os acks exatos de 28/08 ficam de fora).

## Passo 0 — obter o repo nesta box

```bash
sudo dnf install -y git
sudo git clone git@github.com:maxferreira01/citadelp.git /opt/citadelp   # ou https com token
cd /opt/citadelp && git log -1 --oneline
```

Se o clone não tiver o diretório `backend/app/corvo/datadog.py` (push ainda
pendente do laptop), o fallback é copiar do laptop:
`scp -r <laptop>:~/Documents/monitoramento12/citadelp /opt/citadelp` (sem o `.venv`).

## Passo 1 — pré-checagens (1 min)

```bash
python3.11 --version || sudo dnf install -y python3.11          # >= 3.11 obrigatório
curl -s -o /dev/null -w 'slack.com %{http_code}\n' https://slack.com/api/api.test
python3.11 - <<'PY'
import socket; s = socket.create_connection(("wss-primary.slack.com", 443), timeout=5); print("wss-primary.slack.com:443 OK"); s.close()
PY
dnf list installed pango 2>/dev/null | tail -1 || echo "pango ausente — install.sh tenta instalar; sem ele o PDF vira HTML"
```

Leitura: `slack.com 200` e `wss-primary OK` = rede pronta. Se o WSS falhar,
**pare** — Socket Mode não sobe sem ele (é a única porta que o bot precisa; sem
URL pública, sem inbound).

## Passo 2 — instalar (o comando único)

```bash
cd /opt/citadelp && sudo bash deploy/systemd/install.sh
```

O script é idempotente: deps (python3.11, pango, fontes), usuário de sistema
`citadel`, venv com `backend[dev,bot,report]`, `.env` a partir do `.env.example`,
units em `/etc/systemd/system/`, timer habilitado, smoke test offline. Na
primeira execução ele **avisa que os tokens não estão preenchidos** e não sobe o
bot — esperado.

## Passo 3 — `.env` (segredos)

Copie o `.env` do laptop (tem os tokens e as demais chaves do citadelp) **ou**
preencha à mão:

```bash
# opção A — copiar do laptop
scp <laptop>:~/Documents/monitoramento12/citadelp/.env /tmp/citadel.env && sudo install -o citadel -g citadel -m 0600 /tmp/citadel.env /opt/citadelp/.env && rm -f /tmp/citadel.env

# opção B — editar
sudo -u citadel vi /opt/citadelp/.env
```

Chaves que importam para o Corvo (as outras podem ficar como estão):

```bash
SLACK_BOT_TOKEN=xoxb-…                 # Bot User OAuth Token do app Corvo
SLACK_APP_TOKEN=xapp-…                 # App-Level Token (connections:write)
CORVO_DATADOG_CHANNEL_ID=C087SV98MBM
CORVO_DATADOG_BOT_USER=U07Q4UQU0GM
CORVO_REPORT_TO=U053RFRVBE1            # 1ª semana: só o Max; depois U3BBS1RA6,U053RFRVBE1
CORVO_BOT_ALLOWED_USERS=U3BBS1RA6,U053RFRVBE1,U0BNN1BQRAP   # Bruno, Max, Wendell
```

Depois: `sudo bash deploy/systemd/install.sh` de novo — agora ele sobe o bot.

## Passo 4 — validar (5 min)

```bash
systemctl status corvo-datadog-bot --no-pager | head -5       # active (running)
journalctl -u corvo-datadog-bot -n 20 --no-pager              # "gap-fill: N pages" e "Bolt app is running!"
systemctl list-timers 'corvo-datadog-*' --no-pager            # próximo disparo 08:00 America/Sao_Paulo

# 1º scan: 30 dias para popular recorrência (não posta nada)
sudo -u citadel /opt/citadelp/.venv/bin/python /opt/citadelp/collectors/corvo_datadog_report.py --dry-run --scan-days 30 --dump-raw
#   → esperado: "scan: ~600 pages … " e NENHUMA linha "ATENÇÃO: … não parseadas"

# envio de teste só para o Max
sudo -u citadel /opt/citadelp/.venv/bin/python /opt/citadelp/collectors/corvo_datadog_report.py --send --to U053RFRVBE1
```

Na DM do Corvo (no Slack): `ajuda`, `plantão`, `mês`, `tempo médio 7d`. Se
responder, está pronto. Confirme em seguida que os eventos ao vivo chegam:

```bash
journalctl -u corvo-datadog-bot -f      # ao surgir/mudar uma page: "canal: page" / "canal: transition:Triggered->Acknowledged"
sqlite3 /opt/citadelp/data/corvo_datadog.sqlite "select status, source, count(*) from transitions group by 1,2"
```

Depois de um dia com `source='live'` aparecendo, mude `CORVO_REPORT_TO` para
incluir o Bruno (`U3BBS1RA6,U053RFRVBE1`) — o timer faz o resto. Não precisa
reiniciar nada para o timer (ele lê o `.env` a cada execução); para o bot,
`systemctl restart corvo-datadog-bot` só se mudar `CORVO_BOT_ALLOWED_USERS`.

## Passo 5 — desligar o bot do laptop

Assim que o bot daqui estiver `running`, o do laptop precisa parar (dois bots
com o mesmo app-token funcionam, mas os dois respondem cada DM). No laptop:
`kill $(cat <scratchpad>/corvo-bot.pid)` — o Max sabe onde está.

## Se algo der errado

| Sintoma | Ação |
|---|---|
| `channel_not_found` / `not_in_channel` | bot fora do canal: `/invite @corvo` no `#datadog-redes` |
| bot reinicia em loop (`Restart=always`) | `journalctl -u corvo-datadog-bot -n 50`; causa nº 1 é WSS bloqueado, nº 2 token inválido (`invalid_auth`) |
| `weasyprint não importa` | `sudo dnf install -y pango dejavu-sans-fonts` e re-rodar o install; até lá o relatório vai em HTML |
| "mensagens do bot não parseadas" > 0 | Datadog mudou o template: abra `relatorios/corvo-datadog/<data>/raw.json`, ajuste `backend/app/corvo/datadog.py` + fixtures, `make test` |
| DM não chega | `CORVO_REPORT_TO` errado ou app sem `im:write` (manifesto tem); teste `--send --to <seu U>` |

Atualizar código depois: `cd /opt/citadelp && sudo -u citadel git pull && sudo bash deploy/systemd/install.sh`.

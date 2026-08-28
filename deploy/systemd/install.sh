#!/usr/bin/env bash
# install.sh — instala/atualiza o Corvo · Datadog (bot + relatório diário) numa dev-redes.
#
# O que faz (idempotente; re-rode após `git pull`):
#   1. Dependências de sistema: python3.11+, git, pango + fontes (weasyprint) — RHEL (dnf) e Ubuntu (apt)
#   2. Usuário de sistema (default: citadel) dono do repo, data/ e relatorios/
#   3. venv em <repo>/.venv com `pip install -e "backend[dev,bot,report]"`
#   4. .env a partir de .env.example se não existir (chmod 600) — EDITE os tokens
#   5. Units systemd (bot.service, report.service, report.timer) com caminhos do repo
#   6. daemon-reload + enable --now + smoke test (--dry-run --offline)
#
# Uso (na raiz do clone):
#   sudo bash deploy/systemd/install.sh                 # usuário 'citadel'
#   sudo CORVO_USER=maxferreira bash deploy/systemd/install.sh
#
# Atualizar: git pull && sudo bash deploy/systemd/install.sh   (reinicia o bot)

set -euo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
CORVO_USER="${CORVO_USER:-citadel}"
PY="${PYTHON:-}"
UNITS=(corvo-datadog-bot.service corvo-datadog-report.service corvo-datadog-report.timer)

log()  { echo -e "\n\033[1;36m==> $*\033[0m"; }
ok()   { echo -e "    \033[0;32m[OK]\033[0m $*"; }
err()  { echo -e "    \033[0;31m[ERRO]\033[0m $*" >&2; }
warn() { echo -e "    \033[0;33m[WARN]\033[0m $*" >&2; }

[ "$(id -u)" = "0" ] || { err "rode como root (sudo)"; exit 1; }
[ -f "$REPO/collectors/corvo_datadog_bot.py" ] || { err "repo não encontrado em $REPO"; exit 1; }

log "Dependências de sistema"
if command -v dnf >/dev/null 2>&1; then
    dnf install -y -q python3.11 python3.11-pip git pango dejavu-sans-fonts || \
        warn "dnf falhou parcialmente — se faltar pango o PDF vira HTML (o job segue)"
    PY=${PY:-$(command -v python3.11 || command -v python3.12 || command -v python3)}
elif command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-venv git libpango-1.0-0 libpangoft2-1.0-0 fonts-dejavu || \
        warn "apt falhou parcialmente"
    PY=${PY:-$(command -v python3.11 || command -v python3.12 || command -v python3)}
else
    err "nem dnf nem apt-get — instale python>=3.11, git, pango manualmente"; exit 1
fi
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), sys.version' || { err "precisa de Python >= 3.11 ($PY)"; exit 1; }
ok "python: $PY"

log "Usuário $CORVO_USER e permissões"
id "$CORVO_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /sbin/nologin "$CORVO_USER"
mkdir -p "$REPO/data" "$REPO/relatorios"
chown -R "$CORVO_USER:$CORVO_USER" "$REPO"
ok "dono do repo: $CORVO_USER"

log "venv em $REPO/.venv"
if [ ! -x "$REPO/.venv/bin/python" ]; then
    sudo -u "$CORVO_USER" "$PY" -m venv "$REPO/.venv"
fi
sudo -u "$CORVO_USER" "$REPO/.venv/bin/python" -m pip install -q --upgrade pip
sudo -u "$CORVO_USER" "$REPO/.venv/bin/python" -m pip install -q -e "$REPO/backend[dev,bot,report]"
if sudo -u "$CORVO_USER" "$REPO/.venv/bin/python" -c 'import weasyprint' 2>/dev/null; then
    ok "weasyprint ok (PDF)"
else
    warn "weasyprint não importa (pango?) — relatório sai em HTML até resolver"
fi

log "Configuração $REPO/.env"
if [ -f "$REPO/.env" ]; then
    ok "já existe — mantendo"
else
    cp "$REPO/.env.example" "$REPO/.env"
    warn "criado a partir do .env.example — EDITE SLACK_BOT_TOKEN, SLACK_APP_TOKEN e CORVO_REPORT_TO"
fi
chown "$CORVO_USER:$CORVO_USER" "$REPO/.env"; chmod 600 "$REPO/.env"
for v in SLACK_BOT_TOKEN SLACK_APP_TOKEN; do
    if ! grep -qE "^${v}=x(oxb|app)-[A-Za-z0-9-]{10,}" "$REPO/.env"; then
        warn "$v ainda não está preenchido no .env (o bot não sobe sem ele)"
    fi
done

log "Units systemd"
for u in "${UNITS[@]}"; do
    sed -e "s#__REPO__#${REPO}#g" -e "s#__USER__#${CORVO_USER}#g" "$REPO/deploy/systemd/$u" \
        > "/etc/systemd/system/$u"
    ok "$u"
done
systemctl daemon-reload
systemctl enable corvo-datadog-report.timer >/dev/null 2>&1 && systemctl start corvo-datadog-report.timer
if grep -qE "^SLACK_APP_TOKEN=xapp-[A-Za-z0-9-]{10,}" "$REPO/.env"; then
    systemctl enable corvo-datadog-bot.service >/dev/null 2>&1
    systemctl restart corvo-datadog-bot.service
    ok "bot (re)iniciado"
else
    warn "bot NÃO iniciado: preencha SLACK_APP_TOKEN e rode: systemctl enable --now corvo-datadog-bot"
fi

log "Smoke test (offline, sem postar)"
sudo -u "$CORVO_USER" "$REPO/.venv/bin/python" "$REPO/collectors/corvo_datadog_report.py" \
    --offline --dry-run --no-pdf >/dev/null && ok "relatório offline gerado em $REPO/relatorios/corvo-datadog/"

log "Pronto"
systemctl list-timers 'corvo-datadog-*' --no-pager || true
systemctl --no-pager --lines=0 status corvo-datadog-bot.service 2>/dev/null | head -3 || true
echo "    Próximos passos: convidar o bot no #datadog-redes, rodar o 1º scan"
echo "    (sudo -u $CORVO_USER $REPO/.venv/bin/python collectors/corvo_datadog_report.py --dry-run --scan-days 30)"
echo "    e testar o envio: ... --send --to <seu U…>"

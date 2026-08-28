#!/usr/bin/env python3
"""CITADEL · CORVO — bot Slack (Socket Mode) do #datadog-redes.

Sempre ligado (systemd corvo-datadog-bot.service): grava transições das pages
(message_changed → ack/resolve exatos), replies, reações e handovers no store,
e responde comandos na DM (ajuda, hoje, ontem, 7d, 30d, plantão, mês, tempo
médio, top dc, recorrentes, sem resposta, alerta <id>, reenviar pdf).

Uso:
    python collectors/corvo_datadog_bot.py        # precisa de SLACK_BOT_TOKEN e SLACK_APP_TOKEN
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.corvo.bot_app import run  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run())

"""Corvo — configuração via ambiente (.env na raiz do repo, nunca commitado)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]  # <repo>/backend/app/corvo → <repo>


def carregar_env(env_path: Path | None = None) -> None:
    """Carrega o .env da raiz sem sobrescrever o que já veio do ambiente
    (mesmo padrão de scripts/aci_portmap.py; sem python-dotenv)."""
    env = env_path or RAIZ / ".env"
    if not env.is_file():
        return
    for linha in env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


def _lista(v: str | None) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


@dataclass
class Settings:
    slack_bot_token: str | None
    slack_app_token: str | None
    channel_id: str
    datadog_bot_user: str
    report_to: list[str]
    allowed_users: list[str]
    data_dir: Path
    report_dir: Path
    response_window_s: int
    self_user: str | None = None  # preenchido por auth.test no bot
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> Settings:
        carregar_env(env_path)
        g = os.environ.get
        report_to = _lista(g("CORVO_REPORT_TO"))
        allowed = _lista(g("CORVO_BOT_ALLOWED_USERS")) or list(report_to)
        return cls(
            slack_bot_token=g("SLACK_BOT_TOKEN") or None,
            slack_app_token=g("SLACK_APP_TOKEN") or None,
            channel_id=g("CORVO_DATADOG_CHANNEL_ID", "C087SV98MBM"),
            datadog_bot_user=g("CORVO_DATADOG_BOT_USER", "U07Q4UQU0GM"),
            report_to=report_to,
            allowed_users=allowed,
            data_dir=Path(g("CORVO_DATA_DIR") or RAIZ / "data"),
            report_dir=Path(g("CORVO_REPORT_DIR") or RAIZ / "relatorios" / "corvo-datadog"),
            response_window_s=int(g("CORVO_RESPONSE_WINDOW_S", "1800")),
        )

    @property
    def db_path(self) -> Path:
        return self.data_dir / "corvo_datadog.sqlite"

    def token_ok(self) -> bool:
        return bool(self.slack_bot_token) and "TROQUE" not in self.slack_bot_token

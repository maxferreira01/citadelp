"""CITADEL · NSX — config do read-model de capacity de T1.

O citadel NÃO coleta NSX: lê o que o ``nsx-collector`` (Go, 1 instância por
site nas dev-redes) já grava no InfluxDB central. Este módulo só conhece o
Influx e — para o CLI ``--validar``/``--com-edge`` — os Managers em modo GET.

Config (JSON inline, molde do ``aci/config.py``):
    CITADEL_INFLUX='{"url":"http://10.114.35.75:8086","org":"TOTVS",
                     "bucket_nsx":"nsx","bucket_capacity":"nsx_capacity"}'
    CITADEL_INFLUX_TOKEN='<token somente-leitura>'
    CITADEL_NSX_SITE_ALIASES='{"TESP06":"TESP6","TESP07":"TESP7"}'
    CITADEL_NSX_MANAGERS='[{"id":"TESP6","url":"https://<mgr>",
        "user_env":"NSX_TESP6_USER","password_env":"NSX_TESP6_PASS","verify_tls":false}]'

Aliases: a tag ``site`` já coexistiu como TESP06/TESP6, TESP07/TESP7 (validado
em 25/08/2026: hoje só a forma sem zero é escrita, mas o histórico de
``nsx_t1_event`` de jun/2026 ainda carrega TESP06/TESP07). O mapa vai de
variante → canônico; toda leitura normaliza e toda query expande.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field


class NsxConfigError(RuntimeError):
    """Config de Influx/Managers inválida ou ausente."""


@dataclass(frozen=True)
class InfluxConfig:
    url: str
    org: str
    token: str
    bucket_nsx: str = "nsx"
    bucket_capacity: str = "nsx_capacity"

    @property
    def base(self) -> str:
        return self.url.rstrip("/")


@dataclass(frozen=True)
class Manager:
    """NSX Manager de um site — usado SOMENTE para GET (validação)."""

    id: str
    url: str
    user_env: str
    password_env: str
    verify_tls: bool = True

    @property
    def base(self) -> str:
        return self.url.rstrip("/")

    def credenciais(self) -> tuple[str, str]:
        user, pwd = os.environ.get(self.user_env, ""), os.environ.get(self.password_env, "")
        if not user or not pwd:
            raise NsxConfigError(
                f"[{self.id}] credencial ausente: defina {self.user_env}/{self.password_env}"
            )
        return user, pwd


@dataclass(frozen=True)
class Aliases:
    """variante → site canônico. Sites sem alias mapeiam para si mesmos."""

    mapa: dict[str, str] = field(default_factory=dict)

    def canonico(self, site: str) -> str:
        return self.mapa.get(site, site)

    def variantes(self, site: str) -> list[str]:
        canon = self.canonico(site)
        outras = sorted(v for v, c in self.mapa.items() if c == canon)
        return [canon, *[v for v in outras if v != canon]]

    def regex(self, site: str) -> str:
        """Regex Flux ancorada que casa o canônico e todas as variantes.

        Cada nome é escapado — o site vem de query string, nunca vai cru
        para dentro do Flux.
        """
        alts = "|".join(re.escape(v) for v in self.variantes(site))
        return f"^({alts})$"


def _json(env_name: str, default: str):
    raw = os.environ.get(env_name, default)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NsxConfigError(f"{env_name} inválido: {exc}") from exc


def load_influx(env: str | None = None, token: str | None = None) -> InfluxConfig:
    if env is not None:
        try:
            item = json.loads(env)
        except json.JSONDecodeError as exc:
            raise NsxConfigError(f"CITADEL_INFLUX inválido: {exc}") from exc
    else:
        if not os.environ.get("CITADEL_INFLUX"):
            raise NsxConfigError("CITADEL_INFLUX ausente")
        item = _json("CITADEL_INFLUX", "{}")
    tok = token if token is not None else os.environ.get("CITADEL_INFLUX_TOKEN", "")
    if not tok:
        raise NsxConfigError("CITADEL_INFLUX_TOKEN ausente")
    try:
        return InfluxConfig(token=tok, **item)
    except TypeError as exc:
        raise NsxConfigError(f"CITADEL_INFLUX: campos inválidos ({exc})") from exc


def load_aliases(env: str | None = None) -> Aliases:
    if env is not None:
        try:
            mapa = json.loads(env)
        except json.JSONDecodeError as exc:
            raise NsxConfigError(f"CITADEL_NSX_SITE_ALIASES inválido: {exc}") from exc
    else:
        mapa = _json("CITADEL_NSX_SITE_ALIASES", "{}")
    if not isinstance(mapa, dict):
        raise NsxConfigError("CITADEL_NSX_SITE_ALIASES deve ser um objeto variante→canônico")
    return Aliases({str(k): str(v) for k, v in mapa.items()})


def load_managers(env: str | None = None) -> dict[str, Manager]:
    if env is not None:
        try:
            items = json.loads(env)
        except json.JSONDecodeError as exc:
            raise NsxConfigError(f"CITADEL_NSX_MANAGERS inválido: {exc}") from exc
    else:
        items = _json("CITADEL_NSX_MANAGERS", "[]")
    out: dict[str, Manager] = {}
    for item in items:
        try:
            m = Manager(**item)
        except TypeError as exc:
            raise NsxConfigError(f"CITADEL_NSX_MANAGERS: campos inválidos ({exc})") from exc
        out[m.id] = m
    return out

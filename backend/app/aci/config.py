"""CITADEL · ACI — registro dos fabrics (um APIC por parque/edge).

Espelho do modelo de ``checkmk/gateway.py``: config em JSON numa variável de
ambiente, segredos NUNCA no repositório. Cada fabric carrega também o ``cmk_site``
— o id do site Checkmk (de CITADEL_CHECKMK_SITES) que monitora os leafs daquele
parque; é a ponte entre o mapa de portas e as regras de silenciamento.

Config (JSON em CITADEL_ACI_FABRICS):
    [{"id": "TESP6", "apic_url": "https://10.114.35.100",
      "user": "admin", "secret": "...", "verify_tls": false, "cmk_site": "tesp6"}]
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


class AciConfigError(RuntimeError):
    """Config de fabrics inválida ou ausente."""


@dataclass(frozen=True)
class Fabric:
    id: str
    apic_url: str  # https://<ip-ou-fqdn> (sem /api)
    user: str
    secret: str
    # APICs do parque usam certificado self-signed — o default seguro é True,
    # mas o .env real precisa desligar explicitamente.
    verify_tls: bool = True
    cmk_site: str | None = None
    # Regex extra por fabric para reconhecer NSX edge node no sysName do LLDP,
    # quando a convenção local fugir do padrão global.
    padrao_nsx: str | None = None

    @property
    def base(self) -> str:
        return self.apic_url.rstrip("/")


def load_fabrics(env: str | None = None) -> dict[str, Fabric]:
    raw = env if env is not None else os.environ.get("CITADEL_ACI_FABRICS", "[]")
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AciConfigError(f"CITADEL_ACI_FABRICS inválido: {exc}") from exc
    out: dict[str, Fabric] = {}
    for item in items:
        f = Fabric(**item)
        out[f.id] = f
    return out

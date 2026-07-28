"""CITADEL · CORVO — gateway federador da REST API do Checkmk.

Cada edge tem seu próprio site Checkmk (descentralizado). Este gateway registra
os sites via variável de ambiente e normaliza as operações que o Citadel expõe:
criar hosts/monitorações, rodar service discovery, ativar mudanças e
agendar/remover downtimes (inclusive em lote, vinculados a uma RDM — resposta
direta ao storm de 24-25 mai, quando o silêncio por schedule falhou).

Autenticação: automation user por site, header ``Authorization: Bearer user secret``
(formato da REST API 2.x). Credenciais SÓ via ambiente — nunca no repositório.

Config (JSON em CITADEL_CHECKMK_SITES):
    [{"id": "tesp03", "url": "https://cmk-tesp03.interno/tesp03",
      "user": "citadel_api", "secret": "..."}]
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

BRT = timezone(timedelta(hours=-3))


class CheckmkError(RuntimeError):
    """Erro de API com contexto do site e do endpoint."""

    def __init__(self, site: str, detail: str, status: int | None = None):
        super().__init__(f"[{site}] {detail}")
        self.site, self.status = site, status


@dataclass(frozen=True)
class Site:
    id: str
    url: str  # https://host/site (sem /check_mk)
    user: str
    secret: str

    @property
    def base(self) -> str:
        return self.url.rstrip("/") + "/check_mk/api/1.0"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.user} {self.secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


def load_sites(env: str | None = None) -> dict[str, Site]:
    raw = env if env is not None else os.environ.get("CITADEL_CHECKMK_SITES", "[]")
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CheckmkError("registry", f"CITADEL_CHECKMK_SITES inválido: {exc}") from exc
    return {s["id"]: Site(**s) for s in items}


class Gateway:
    """Cliente por site. ``transport`` injetável para testes (MockTransport)."""

    def __init__(
        self,
        site: Site,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 20.0,
    ):
        self.site = site
        self._c = httpx.Client(
            base_url=site.base,
            headers=site.headers,
            timeout=timeout,
            transport=transport,
            verify=True,
        )

    # ------------------------------------------------------------------ util
    def _req(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        try:
            r = self._c.request(method, path, json=json_body, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise CheckmkError(self.site.id, f"falha de rede em {path}: {exc}") from exc
        if r.status_code >= 400:
            raise CheckmkError(
                self.site.id, f"{method} {path} → {r.status_code}: {r.text[:300]}", r.status_code
            )
        return r.json() if r.content else {}

    # ------------------------------------------------- hosts / monitorações
    def create_host(
        self,
        host_name: str,
        folder: str = "/",
        ipaddress: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> dict:
        """Cria o host (nova monitoração). Depois: discover() + activate()."""
        attrs: dict[str, Any] = {}
        if ipaddress:
            attrs["ipaddress"] = ipaddress
        if labels:
            attrs["labels"] = labels
        return self._req(
            "POST",
            "/domain-types/host_config/collections/all",
            json_body={"folder": folder, "host_name": host_name, "attributes": attrs},
        )

    def discover(self, host_name: str, mode: str = "fix_all") -> dict:
        """Service discovery (fix_all = aceita novos serviços e remove sumidos)."""
        return self._req(
            "POST",
            "/domain-types/service_discovery_run/actions/start/invoke",
            json_body={"host_name": host_name, "mode": mode},
        )

    def activate(self, force_foreign: bool = False) -> dict:
        """Ativa mudanças pendentes no site (If-Match "*" cobre o ETag exigido)."""
        return self._req(
            "POST",
            "/domain-types/activation_run/actions/activate-changes/invoke",
            json_body={"redirect": False, "sites": [], "force_foreign_changes": force_foreign},
            headers={"If-Match": "*"},
        )

    # -------------------------------------------------------------- downtimes
    def schedule_downtime(
        self,
        host_name: str,
        minutes: int,
        comment: str,
        services: list[str] | None = None,
        start: datetime | None = None,
    ) -> dict:
        """Downtime de host (services=None) ou de serviços específicos."""
        t0 = (start or datetime.now(BRT)).isoformat()
        t1 = ((start or datetime.now(BRT)) + timedelta(minutes=minutes)).isoformat()
        if services:
            body = {
                "downtime_type": "service",
                "host_name": host_name,
                "service_descriptions": services,
                "start_time": t0,
                "end_time": t1,
                "comment": comment,
            }
            path = "/domain-types/downtime/collections/service"
        else:
            body = {
                "downtime_type": "host",
                "host_name": host_name,
                "start_time": t0,
                "end_time": t1,
                "comment": comment,
            }
            path = "/domain-types/downtime/collections/host"
        return self._req("POST", path, json_body=body)

    def list_downtimes(self, host_name: str | None = None) -> list[dict]:
        params = {"host_name": host_name} if host_name else None
        data = self._req("GET", "/domain-types/downtime/collections/all", params=params)
        return data.get("value", [])

    def delete_downtime(self, downtime_id: str) -> dict:
        return self._req(
            "POST",
            "/domain-types/downtime/actions/delete/invoke",
            json_body={"delete_type": "by_id", "downtime_id": downtime_id},
        )

    def close(self) -> None:
        self._c.close()


def rdm_downtime(
    sites: dict[str, Site],
    plan: list[dict],
    rdm: str,
    minutes: int,
    transport: httpx.BaseTransport | None = None,
) -> list[dict]:
    """Downtime em lote vinculado a uma RDM, cruzando sites descentralizados.

    plan: [{"site": "tesp03", "host": "edge-fw01", "services": ["Float IP"] | None}]
    Retorna um recibo por item (ok/erro) — nunca interrompe o lote no 1º erro.
    """
    receipts: list[dict] = []
    comment = f"RDM {rdm} · downtime via CITADEL"
    for item in plan:
        sid = item["site"]
        if sid not in sites:
            receipts.append(
                {"site": sid, "host": item.get("host"), "ok": False, "error": "site não registrado"}
            )
            continue
        gw = Gateway(sites[sid], transport=transport)
        try:
            gw.schedule_downtime(item["host"], minutes, comment, item.get("services"))
            receipts.append({"site": sid, "host": item["host"], "ok": True, "rdm": rdm})
        except CheckmkError as exc:
            receipts.append({"site": sid, "host": item["host"], "ok": False, "error": str(exc)})
        finally:
            gw.close()
    return receipts

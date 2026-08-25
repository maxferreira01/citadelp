"""CITADEL · NSX — leitura direta do NSX Manager, SOMENTE GET.

Existe para o cross-check do CLI (``--validar``: Manager × Influx) e para o
agregado por edge cluster (``--com-edge``) enquanto o collector não persiste
essa série. Basic auth (como o collector Go). Em 401/403 não insiste: tentativa
repetida com credencial errada é o que bloqueia a conta de serviço.

Não há e não deve haver método de escrita aqui.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import httpx

from .config import Manager
from .modelos import T1PorEdge

PAGE = 1000


class ManagerError(RuntimeError):
    def __init__(self, site: str, detail: str, status: int | None = None):
        super().__init__(f"[{site}] {detail}")
        self.site, self.status = site, status


class ManagerClient:
    def __init__(
        self,
        mgr: Manager,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 60.0,
    ):
        self.mgr = mgr
        user, pwd = mgr.credenciais()
        self._c = httpx.Client(
            base_url=mgr.base,
            timeout=timeout,
            transport=transport,
            verify=mgr.verify_tls,
            auth=(user, pwd),
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            r = self._c.get(path, params=params)
        except httpx.HTTPError as exc:
            raise ManagerError(self.mgr.id, f"falha de rede em {path}: {exc}") from exc
        if r.status_code in (401, 403):
            raise ManagerError(
                self.mgr.id,
                f"GET {path} → {r.status_code}: credencial recusada — NÃO repetir (lockout)",
                r.status_code,
            )
        if r.status_code != 200:
            raise ManagerError(
                self.mgr.id, f"GET {path} → {r.status_code}: {r.text[:200]}", r.status_code
            )
        return r.json()

    def paginado(self, path: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": PAGE}
            if cursor:
                params["cursor"] = cursor
            data = self.get(path, params)
            out.extend(data.get("results", []))
            cursor = data.get("cursor")
            if not cursor:
                return out

    # ------------------------------------------------------------ consultas
    def total_tier1(self) -> int:
        """``result_count`` já é o total; uma página de 1 basta."""
        data = self.get("/policy/api/v1/infra/tier-1s", {"page_size": 1})
        return int(data.get("result_count", 0))

    def capacity_tier1(self) -> dict[str, Any]:
        data = self.get("/api/v1/capacity/usage")
        for item in data.get("capacity_usage", []):
            if item.get("usage_type") == "NUMBER_OF_TIER1_ROUTERS":
                return {
                    "current": int(item.get("current_usage_count", 0)),
                    "max": int(item.get("max_supported_count", 0)),
                    "pct": float(item.get("current_usage_percentage", 0.0)),
                    "severity": item.get("severity", ""),
                }
        raise ManagerError(self.mgr.id, "capacity/usage sem NUMBER_OF_TIER1_ROUTERS")

    def tier1s(self) -> list[dict[str, Any]]:
        return self.paginado("/policy/api/v1/infra/tier-1s")

    def por_edge_cluster(self) -> list[T1PorEdge]:
        """Join logical-routers(TIER1) → edge_cluster_id → nome do cluster."""
        nomes = {
            ec.get("id"): ec.get("display_name", ec.get("id"))
            for ec in self.get(
                "/policy/api/v1/infra/sites/default/enforcement-points/default/edge-clusters"
            ).get("results", [])
        }
        cont: Counter[str] = Counter()
        for lr in self.paginado("/api/v1/logical-routers"):
            if lr.get("router_type") != "TIER1":
                continue
            cont[lr.get("edge_cluster_id") or ""] += 1
        return sorted(
            (
                T1PorEdge(
                    site=self.mgr.id,
                    edge_cluster_name=nomes.get(ecid, "(sem edge cluster)" if not ecid else ecid),
                    edge_cluster_id=ecid,
                    t1_count=n,
                )
                for ecid, n in cont.items()
            ),
            key=lambda e: -e.t1_count,
        )

    def close(self) -> None:
        self._c.close()

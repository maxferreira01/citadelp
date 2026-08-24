"""CITADEL · ACI — cliente REST do APIC (somente leitura).

Porta do cliente Go do aci-lldp-collector, com as mesmas decisões que lá foram
aprendidas na prática:

- Login por ``POST /api/aaaLogin.json`` → token em cookie ``APIC-cookie``;
  renovação antecipada (margem de 30 s sobre o refreshTimeoutSeconds).
- Paginação por ``page``/``page-size`` acumulando até ``totalCount``.
- Consultas de subtree SEMPRE per-node: o endpoint bulk
  ``/api/node/class/lldpAdjEp.json`` desta versão de APIC duplica registros
  entre páginas e OMITE nós inteiros (node-1002/1004/1020/1021/1022/1025/
  1034/1035/1040/1041/1043 no TESP6, verificado). O per-node é o único caminho
  confiável; a dedup por DN completo fica no chamador como cinto-e-suspensório.
- Concorrência limitada a 8 requisições simultâneas para não estressar o APIC.

Este cliente NÃO tem métodos de escrita — equipamento é somente leitura.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from .config import Fabric

TAM_PAGINA = 200
MARGEM_RENOVACAO_S = 30
MAX_CONCORRENCIA = 8


class AciError(RuntimeError):
    """Erro de API com contexto do fabric e do path."""

    def __init__(self, fabric: str, detail: str, status: int | None = None):
        super().__init__(f"[{fabric}] {detail}")
        self.fabric, self.status = fabric, status


class AciClient:
    """Cliente por fabric. ``transport`` injetável para testes (MockTransport)."""

    def __init__(
        self,
        fabric: Fabric,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
    ):
        self.fabric = fabric
        self._c = httpx.Client(
            base_url=fabric.base,
            timeout=timeout,
            transport=transport,
            verify=fabric.verify_tls,
        )
        self._lock = threading.Lock()
        self._token = ""
        self._token_exp = 0.0

    # ------------------------------------------------------------------ auth
    def _login(self) -> None:
        body = {"aaaUser": {"attributes": {"name": self.fabric.user, "pwd": self.fabric.secret}}}
        try:
            r = self._c.post("/api/aaaLogin.json", json=body)
        except httpx.HTTPError as exc:
            raise AciError(self.fabric.id, f"falha de rede no login: {exc}") from exc
        if r.status_code == 401:
            # 401 no login = credencial recusada. Não insistir: repetição de
            # tentativa errada é o que trava conta no AAA.
            raise AciError(self.fabric.id, "login recusado (401) — conferir credencial", 401)
        if r.status_code != 200:
            raise AciError(
                self.fabric.id, f"login → {r.status_code}: {r.text[:200]}", r.status_code
            )
        try:
            attrs = r.json()["imdata"][0]["aaaLogin"]["attributes"]
            token = attrs["token"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise AciError(self.fabric.id, f"resposta de login sem token: {exc}") from exc
        try:
            refresh = int(attrs.get("refreshTimeoutSeconds", "300"))
        except ValueError:
            refresh = 300
        self._token = token
        self._token_exp = time.monotonic() + max(refresh - MARGEM_RENOVACAO_S, 60)

    def _ensure_auth(self) -> str:
        with self._lock:
            if not self._token or time.monotonic() >= self._token_exp:
                self._login()
            return self._token

    # ------------------------------------------------------------------- get
    def get(self, path: str) -> dict[str, Any]:
        token = self._ensure_auth()
        try:
            r = self._c.get(path, headers={"Cookie": f"APIC-cookie={token}"})
        except httpx.HTTPError as exc:
            raise AciError(self.fabric.id, f"falha de rede em {path}: {exc}") from exc
        if r.status_code == 403:
            # token expirou no meio de uma varredura longa — renova uma vez
            with self._lock:
                self._login()
                token = self._token
            r = self._c.get(path, headers={"Cookie": f"APIC-cookie={token}"})
        if r.status_code != 200:
            raise AciError(
                self.fabric.id, f"GET {path} → {r.status_code}: {r.text[:200]}", r.status_code
            )
        return r.json()

    def get_all_pages(self, path: str) -> list[dict[str, Any]]:
        """Todos os objetos ``imdata`` de uma consulta, atravessando as páginas."""
        sep = "&" if "?" in path else "?"
        out: list[dict[str, Any]] = []
        page = 0
        while True:
            data = self.get(f"{path}{sep}page={page}&page-size={TAM_PAGINA}")
            out.extend(data.get("imdata", []))
            try:
                total = int(data.get("totalCount", "0"))
            except ValueError:
                total = 0
            if total == 0 or len(out) >= total:
                return out
            page += 1

    def por_no(
        self, alvos: list[tuple[str, str]], monta_path, max_workers: int = MAX_CONCORRENCIA
    ) -> list[list[dict[str, Any]]]:
        """Roda ``get_all_pages(monta_path(pod, node_id))`` para cada nó, em paralelo.

        Qualquer nó com erro derruba a coleta inteira do fabric: mapa parcial
        silenciosamente incompleto é pior que falha explícita — é a mesma
        posição do coletor Go.
        """
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futs = [pool.submit(self.get_all_pages, monta_path(pod, node)) for pod, node in alvos]
            return [f.result() for f in futs]

    def close(self) -> None:
        self._c.close()

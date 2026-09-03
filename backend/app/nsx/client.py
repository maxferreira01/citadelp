"""CITADEL · NSX — cliente Flux do InfluxDB (somente consulta).

``POST /api/v2/query?org=`` com corpo JSON (query + dialect com anotações) e
parse do CSV anotado que o Influx devolve: várias tabelas por resposta, cada
uma com suas linhas ``#datatype/#group/#default`` seguidas do cabeçalho.
Valores voltam tipados (long→int, double→float, boolean→bool); o resto fica
string (dateTime:RFC3339 inclusive — quem consome formata).

``transport`` injetável para testes (httpx.MockTransport). Nenhum método de
escrita: o citadel não grava no Influx.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import httpx

from .config import InfluxConfig


class NsxError(RuntimeError):
    """Erro de consulta com contexto."""

    def __init__(self, detail: str, status: int | None = None):
        super().__init__(detail)
        self.status = status


def _conv(tipo: str, valor: str) -> Any:
    if valor == "":
        return None
    if tipo == "long" or tipo == "unsignedLong":
        try:
            return int(valor)
        except ValueError:
            return valor
    if tipo == "double":
        try:
            return float(valor)
        except ValueError:
            return valor
    if tipo == "boolean":
        return valor == "true"
    return valor


def parse_csv_anotado(texto: str) -> list[dict[str, Any]]:
    """Linhas de todas as tabelas, sem as colunas internas ``result``/``table``."""
    out: list[dict[str, Any]] = []
    tipos: list[str] = []
    cabecalho: list[str] | None = None
    for row in csv.reader(io.StringIO(texto)):
        if not row or all(c == "" for c in row):
            cabecalho = None  # nova tabela vem a seguir
            continue
        if row[0].startswith("#"):
            if row[0] == "#datatype":
                tipos = row
            cabecalho = None
            continue
        if cabecalho is None:
            cabecalho = row
            continue
        linha: dict[str, Any] = {}
        for i, nome in enumerate(cabecalho):
            if nome in ("", "result", "table"):
                continue
            tipo = tipos[i] if i < len(tipos) else "string"
            linha[nome] = _conv(tipo, row[i] if i < len(row) else "")
        out.append(linha)
    return out


class InfluxClient:
    def __init__(
        self,
        cfg: InfluxConfig,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 60.0,
    ):
        self.cfg = cfg
        self._c = httpx.Client(
            base_url=cfg.base,
            timeout=timeout,
            transport=transport,
            headers={"Authorization": f"Token {cfg.token}"},
        )

    def query(self, flux: str) -> list[dict[str, Any]]:
        corpo = {
            "query": flux,
            "type": "flux",
            "dialect": {"annotations": ["datatype", "group", "default"], "header": True},
        }
        try:
            r = self._c.post("/api/v2/query", params={"org": self.cfg.org}, json=corpo)
        except httpx.HTTPError as exc:
            raise NsxError(f"falha de rede no Influx: {exc}") from exc
        if r.status_code == 401:
            raise NsxError("Influx recusou o token (401)", 401)
        if r.status_code != 200:
            raise NsxError(f"Influx → {r.status_code}: {r.text[:300]}", r.status_code)
        return parse_csv_anotado(r.text)

    def ping(self) -> bool:
        try:
            r = self._c.get("/health")
        except httpx.HTTPError as exc:
            raise NsxError(f"falha de rede no Influx: {exc}") from exc
        return r.status_code == 200

    def close(self) -> None:
        self._c.close()

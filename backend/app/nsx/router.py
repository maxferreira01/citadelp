"""CITADEL · NSX — rotas de LEITURA da capacity de Tier-1.

Tudo aqui é consulta ao InfluxDB central preenchido pelo ``nsx-collector``.
Nenhuma rota toca NSX Manager, e não há escrita em lugar nenhum: o citadel
é read-model. O cross-check contra a Manager (GET) fica no CLI
``scripts/nsx_t1capacity.py --validar``, fora da API de propósito.
"""

from __future__ import annotations

import csv
import io
import json
import re
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from .artefatos import ultimo_snapshot
from .client import InfluxClient, NsxError
from .config import NsxConfigError, load_aliases, load_influx
from .consultas import Consultas

router = APIRouter(prefix="/nsx", tags=["nsx"])

_SITE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


@lru_cache(maxsize=1)
def _consultas() -> Consultas:
    try:
        return Consultas(InfluxClient(load_influx()), load_aliases())
    except NsxConfigError as exc:
        raise HTTPException(503, f"NSX/Influx não configurado: {exc}") from exc


def _site(site: str) -> str:
    if not _SITE_RE.match(site):
        raise HTTPException(422, "site inválido")
    return site


def _run(fn):
    try:
        return fn()
    except NsxError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/t1/resumo")
def resumo(site: str | None = Query(default=None)) -> list[dict]:
    """Por site (normalizado por aliases): totals do collector + capacity NSX.
    A soma de ``total`` de todos os sites é o parque inteiro."""
    q = _consultas()
    return _run(lambda: [r.dict() for r in q.resumo(_site(site) if site else None)])


@router.get("/t1/por-t0")
def por_t0(site: str) -> list[dict]:
    q = _consultas()
    return _run(lambda: [t.dict() for t in q.por_t0(_site(site))])


@router.get("/t1/por-vrf")
def por_vrf(site: str) -> list[dict]:
    q = _consultas()
    return _run(lambda: [v.dict() for v in q.por_vrf(_site(site))])


@router.get("/t1/historico")
def historico(site: str, dias: int = Query(default=30, ge=1, le=365)) -> list[dict]:
    """``nsx_t1_totals.total`` agregado por dia (last) — alimenta a trajetória."""
    q = _consultas()
    return _run(lambda: [p.dict() for p in q.historico(_site(site), dias)])


@router.get("/t1/eventos")
def eventos(site: str, dias: int = Query(default=7, ge=1, le=365)) -> list[dict]:
    q = _consultas()
    return _run(lambda: [e.dict() for e in q.eventos(_site(site), dias)])


@router.get("/t1/snapshot")
def snapshot(site: str) -> dict:
    """Último snapshot gravado pelo CLI (inclui validação e edge clusters, se rodou)."""
    caminho = ultimo_snapshot(_site(site))
    if caminho is None:
        raise HTTPException(404, f"nenhum snapshot gerado para '{site}'")
    return json.loads(caminho.read_text(encoding="utf-8"))


@router.get("/t1/tabela")
def tabela(
    site: str | None = Query(default=None), formato: str = Query(default="json")
) -> list[dict]:
    """Formato da planilha de capacity (Edge/Node/Limite/VRF/Dia/Mes/Ano/Qtd).
    ``formato=csv`` devolve texto para colar na planilha."""
    q = _consultas()
    linhas = _run(lambda: q.tabela(_site(site) if site else None))
    if formato != "csv":
        return linhas
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(
        [
            "Edge",
            "Node",
            "Limite-node",
            "vrf-number",
            "limite-vrf",
            "Dia",
            "Mes",
            "Ano",
            "Qtd-vrf",
            "Qtd-node",
        ]
    )
    for r in linhas:
        w.writerow(
            [
                r["edge"],
                r["node"],
                r["limite_node"],
                r["vrf"],
                r["limite_vrf"],
                r["dia"],
                r["mes"],
                r["ano"],
                r["qtd"],
                r["qtd_node"],
            ]
        )
    return PlainTextResponse(buf.getvalue(), media_type="text/csv; charset=utf-8")

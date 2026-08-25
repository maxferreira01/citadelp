"""CITADEL · NSX — snapshot revisável de capacity de T1 (JSON + CSV).

``relatorios/nsx-t1capacity/<SITE>/t1capacity-<ts>.{json,csv}`` +
``resumo-<ts>.csv``. Diretório no .gitignore. O JSON é o registro; o CSV é
para abrir e revisar; o resumo é a "query diária" em uma tabela
(site × t0/vrf/edge × count/limit/pct).
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .modelos import ResumoSite, T1PorEdge, T1PorT0, T1PorVrf

BRT = timezone(timedelta(hours=-3))
RAIZ_REPO = Path(__file__).resolve().parents[3]

COLUNAS = [
    "site",
    "nivel",
    "nome",
    "parent",
    "t1_count",
    "limit",
    "usage_pct",
    "available",
    "fonte",
]


def _linhas(
    site: str,
    por_t0: list[T1PorT0],
    por_vrf: list[T1PorVrf],
    por_edge: list[T1PorEdge] | None,
) -> list[dict]:
    out: list[dict] = []
    for t in por_t0:
        out.append(
            {
                "site": site,
                "nivel": "t0",
                "nome": t.t0_name,
                "parent": "",
                "t1_count": t.t1_count,
                "limit": t.limit,
                "usage_pct": t.usage_pct,
                "available": t.available,
                "fonte": "OBS · nsx-collector → InfluxDB",
            }
        )
    for v in por_vrf:
        out.append(
            {
                "site": site,
                "nivel": "vrf",
                "nome": v.vrf_name,
                "parent": v.t0_parent,
                "t1_count": v.t1_count,
                "limit": v.limit,
                "usage_pct": v.usage_pct,
                "available": v.available,
                "fonte": "OBS · nsx-collector → InfluxDB",
            }
        )
    for e in por_edge or []:
        out.append(
            {
                "site": site,
                "nivel": "edge_cluster",
                "nome": e.edge_cluster_name,
                "parent": "",
                "t1_count": e.t1_count,
                "limit": "",
                "usage_pct": "",
                "available": "",
                "fonte": "OBS · NSX Manager (GET, CLI --com-edge)",
            }
        )
    return out


def gravar_snapshot(
    site: str,
    resumo: ResumoSite | None,
    por_t0: list[T1PorT0],
    por_vrf: list[T1PorVrf],
    por_edge: list[T1PorEdge] | None = None,
    validacao: dict | None = None,
    base: Path | None = None,
    quando: datetime | None = None,
) -> dict[str, Path]:
    agora = quando or datetime.now(BRT)
    ts = agora.strftime("%Y%m%d-%H%M")
    destino = (base or RAIZ_REPO / "relatorios" / "nsx-t1capacity") / site
    destino.mkdir(parents=True, exist_ok=True)
    linhas = _linhas(site, por_t0, por_vrf, por_edge)

    caminho_json = destino / f"t1capacity-{ts}.json"
    caminho_json.write_text(
        json.dumps(
            {
                "site": site,
                "gerado_em": agora.isoformat(),
                "resumo": resumo.dict() if resumo else None,
                "validacao": validacao,
                "por_t0": [t.dict() for t in por_t0],
                "por_vrf": [v.dict() for v in por_vrf],
                "por_edge_cluster": [e.dict() for e in por_edge] if por_edge is not None else None,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    caminho_csv = destino / f"t1capacity-{ts}.csv"
    with caminho_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    caminho_resumo = destino / f"resumo-{ts}.csv"
    with caminho_resumo.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "site",
                "total",
                "on_t0",
                "on_vrf",
                "nsx_current",
                "nsx_max",
                "nsx_pct",
                "t0s",
                "vrfs",
                "vrfs>=90%",
                "edge_clusters",
            ]
        )
        r = resumo
        w.writerow(
            [
                site,
                r.total if r else "",
                r.on_t0 if r else "",
                r.on_vrf if r else "",
                r.nsx_current if r else "",
                r.nsx_max if r else "",
                r.nsx_pct if r else "",
                len(por_t0),
                len(por_vrf),
                sum(1 for v in por_vrf if v.usage_pct >= 90),
                len(por_edge) if por_edge is not None else "",
            ]
        )
    return {"json": caminho_json, "csv": caminho_csv, "resumo": caminho_resumo}


def ultimo_snapshot(site: str, base: Path | None = None) -> Path | None:
    destino = (base or RAIZ_REPO / "relatorios" / "nsx-t1capacity") / site
    if not destino.is_dir():
        return None
    arquivos = sorted(destino.glob("t1capacity-*.json"))
    return arquivos[-1] if arquivos else None


def gravar_criacao(
    site: str, itens: list[dict], base: Path | None = None, quando: datetime | None = None
) -> Path:
    """``criacao-<ts>.json``: todos os T1 do site com ``_create_time`` (Manager, GET).
    Cada execução é um snapshot novo — a diferença entre dois snapshots revela
    remoções que a API já não mostra."""
    agora = quando or datetime.now(BRT)
    destino = (base or RAIZ_REPO / "relatorios" / "nsx-t1capacity") / site
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"criacao-{agora.strftime('%Y%m%d-%H%M')}.json"
    caminho.write_text(
        json.dumps(
            {"site": site, "gerado_em": agora.isoformat(), "total": len(itens), "t1s": itens},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return caminho


def snapshots_criacao(site: str, base: Path | None = None) -> list[Path]:
    destino = (base or RAIZ_REPO / "relatorios" / "nsx-t1capacity") / site
    return sorted(destino.glob("criacao-*.json")) if destino.is_dir() else []

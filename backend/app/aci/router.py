"""CITADEL · ACI — rotas de LEITURA do mapa de portas.

Servem os artefatos já gerados pelos CLIs (scripts/aci_portmap.py). A escrita
no Checkmk fica fora da API de propósito: aplicar regra é operação gated por
--apply no scripts/aci_silenciar.py, com artefato revisado antes.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from .artefatos import ultimo_portmap
from .config import load_fabrics

router = APIRouter(prefix="/aci", tags=["aci"])


@router.get("/fabrics")
def fabrics() -> list[dict]:
    """Fabrics registrados (sem segredos) e o site Checkmk associado."""
    return [
        {"id": f.id, "apic_url": f.apic_url, "cmk_site": f.cmk_site}
        for f in load_fabrics().values()
    ]


def _mapa(fabric_id: str) -> dict:
    caminho = ultimo_portmap(fabric_id)
    if caminho is None:
        raise HTTPException(404, f"nenhum portmap gerado para '{fabric_id}'")
    return json.loads(caminho.read_text(encoding="utf-8"))


@router.get("/portmap/resumo")
def resumo() -> list[dict]:
    """Contagem por classe, por fabric — visão de painel."""
    out = []
    for fid in load_fabrics():
        caminho = ultimo_portmap(fid)
        if caminho is None:
            out.append({"fabric": fid, "portmap": None})
            continue
        m = json.loads(caminho.read_text(encoding="utf-8"))
        out.append(
            {
                "fabric": fid,
                "gerado_em": m.get("gerado_em"),
                "total_portas": m.get("total_portas"),
                "por_classe": m.get("por_classe", {}),
            }
        )
    return out


@router.get("/portmap")
def portmap(fabric: str) -> dict:
    """Último mapa completo do fabric (o JSON do artefato, como gerado)."""
    return _mapa(fabric)

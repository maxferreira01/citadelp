"""CITADEL · ACI — artefatos do mapa de portas (JSON + CSV revisáveis).

Tudo cai em ``relatorios/aci-portmap/<FABRIC>/`` (diretório no .gitignore:
esses arquivos carregam hostnames e descrições do ambiente). O JSON é o formato
que os estágios seguintes (plano de regras) leem; o CSV existe para o operador
abrir e revisar — em especial as DESCONHECIDAS que ficaram alarmando.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .modelos import PortaMapeada

BRT = timezone(timedelta(hours=-3))
RAIZ_REPO = Path(__file__).resolve().parents[3]

COLUNAS = [
    "fabric",
    "pod",
    "node_id",
    "leaf_name",
    "iface",
    "classe",
    "silenciar",
    "confianca",
    "oper_st",
    "oper_reason",
    "oper_speed",
    "admin_st",
    "usage",
    "bundle",
    "lldp_sysname",
    "lldp_mgmt_ip",
    "lldp_portdesc",
    "epgs",
    "descr",
    "evidencia",
]


def _linha(fabric_id: str, m: PortaMapeada) -> dict[str, str]:
    p, c = m.porta, m.cls
    return {
        "fabric": fabric_id,
        "pod": p.pod,
        "node_id": p.node_id,
        "leaf_name": p.leaf_name,
        "iface": p.iface,
        "classe": c.classe.value,
        "silenciar": "sim" if c.silenciar else "nao",
        "confianca": c.confianca,
        "oper_st": p.oper_st,
        "oper_reason": p.oper_reason,
        "oper_speed": p.oper_speed,
        "admin_st": p.admin_st,
        "usage": p.usage,
        "bundle": p.bundle,
        "lldp_sysname": p.lldp.sys_name if p.lldp else "",
        "lldp_mgmt_ip": p.lldp.mgmt_ip if p.lldp else "",
        "lldp_portdesc": p.lldp.port_desc if p.lldp else "",
        "epgs": ";".join(p.epgs),
        "descr": p.descr,
        "evidencia": " | ".join(c.evidencia),
    }


def gravar_portmap(
    fabric_id: str,
    mapeadas: list[PortaMapeada],
    base: Path | None = None,
    quando: datetime | None = None,
) -> dict[str, Path]:
    """Grava portmap-<ts>.{json,csv} + resumo-<ts>.csv; devolve os paths."""
    ts = (quando or datetime.now(BRT)).strftime("%Y%m%d-%H%M")
    destino = (base or RAIZ_REPO / "relatorios" / "aci-portmap") / fabric_id
    destino.mkdir(parents=True, exist_ok=True)

    linhas = [_linha(fabric_id, m) for m in mapeadas]

    caminho_json = destino / f"portmap-{ts}.json"
    caminho_json.write_text(
        json.dumps(
            {
                "fabric": fabric_id,
                "gerado_em": (quando or datetime.now(BRT)).isoformat(),
                "total_portas": len(linhas),
                "por_classe": dict(Counter(x["classe"] for x in linhas)),
                "portas": linhas,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    caminho_csv = destino / f"portmap-{ts}.csv"
    with caminho_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    # resumo leaf × classe (mesmo espírito dos summaries do survey de portas livres)
    caminho_resumo = destino / f"resumo-{ts}.csv"
    contagem: dict[str, Counter] = {}
    for x in linhas:
        contagem.setdefault(x["leaf_name"] or x["node_id"], Counter())[x["classe"]] += 1
    classes = sorted({c for cnt in contagem.values() for c in cnt})
    with caminho_resumo.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["leaf", *classes, "total"])
        for leaf in sorted(contagem):
            cnt = contagem[leaf]
            w.writerow([leaf, *[cnt.get(c, 0) for c in classes], sum(cnt.values())])

    return {"json": caminho_json, "csv": caminho_csv, "resumo": caminho_resumo}


def ultimo_portmap(fabric_id: str, base: Path | None = None) -> Path | None:
    """O JSON mais recente do fabric, ou None."""
    destino = (base or RAIZ_REPO / "relatorios" / "aci-portmap") / fabric_id
    if not destino.is_dir():
        return None
    arquivos = sorted(destino.glob("portmap-*.json"))
    return arquivos[-1] if arquivos else None

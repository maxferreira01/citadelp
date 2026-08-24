#!/usr/bin/env python3
"""CITADEL · ACI — validação de cobertura: todo leaf ACI está monitorado no Checkmk?

Cruza os leafs dos portmaps já gerados (scripts/aci_portmap.py) com os hosts
LEAF* de CADA site Checkmk registrado em CITADEL_CHECKMK_SITES. Tudo GET —
nada é alterado em lugar nenhum.

Saída: uma linha por leaf (monitorado/não, em qual site, por qual nome) +
hosts LEAF* órfãos nos sites (monitorados no Checkmk sem leaf correspondente
no mapa ACI) + consolidado em relatorios/aci-portmap/cobertura-<ts>.csv.

Uso: python scripts/aci_cobertura.py               # todos os fabrics mapeados
     python scripts/aci_cobertura.py --fabric TESP6
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.aci.artefatos import ultimo_portmap
from app.aci.cmk_match import casar_leafs, descobrir_sites, normalizar_leaf
from app.aci.config import load_fabrics
from app.checkmk.gateway import load_sites

BRT = timezone(timedelta(hours=-3))


def carregar_env() -> None:
    env = RAIZ / ".env"
    if not env.is_file():
        return
    for linha in env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fabric", help="um fabric só (default: todos com portmap gerado)")
    args = ap.parse_args()

    carregar_env()
    fabrics = load_fabrics()
    sites = load_sites()
    if not sites:
        print("CITADEL_CHECKMK_SITES vazio — preencha o .env com os automation users")
        return 2

    alvos = (
        {args.fabric: fabrics[args.fabric]}
        if args.fabric and args.fabric in fabrics
        else fabrics
    )
    if args.fabric and args.fabric not in fabrics:
        print(
            f"fabric '{args.fabric}' não registrado; existem: {', '.join(sorted(fabrics))}"
        )
        return 2

    print("descobrindo sites Checkmk (GET)...")
    descobertos = descobrir_sites(sites)
    for sid, d in sorted(descobertos.items()):
        rotulo = (
            "SEM REST (1.5) — validar pela GUI"
            if d.sem_rest
            else (d.erro or f"{d.versao} — {len(d.hosts_leaf)} hosts LEAF*")
        )
        print(f"  site {sid}: {rotulo}")

    ts = datetime.now(BRT).strftime("%Y%m%d-%H%M")
    caminho = RAIZ / "relatorios" / "aci-portmap" / f"cobertura-{ts}.csv"
    linhas: list[dict] = []
    usados_por_site: dict[str, set[str]] = {}

    for fid, fabric in sorted(alvos.items()):
        art = ultimo_portmap(fid)
        if art is None:
            print(f"\n[{fid}] sem portmap gerado — rode scripts/aci_portmap.py antes")
            continue
        mapa = json.loads(art.read_text(encoding="utf-8"))
        leafs = sorted({p["leaf_name"] for p in mapa["portas"] if p["leaf_name"]})
        matches = casar_leafs(leafs, descobertos, fabric.cmk_site or "")
        cobertos = sum(1 for m in matches if m.host_cmk)
        print(
            f"\n[{fid}] {len(leafs)} leafs no ACI → {cobertos} monitorados no Checkmk"
        )
        for m in matches:
            if m.host_cmk and m.site_id:
                usados_por_site.setdefault(m.site_id, set()).add(m.host_cmk.upper())
            estado = "monitorado" if m.host_cmk else "NAO-MONITORADO"
            if m.host_cmk is None or m.camada != "exato" or "COLISÃO" in m.detalhe:
                print(
                    f"  {estado:<15} {m.leaf_aci:<18} → {m.host_cmk or '-':<18} "
                    f"[{m.camada}] {m.detalhe}"
                )
            linhas.append(
                {
                    "fabric": fid,
                    "leaf_aci": m.leaf_aci,
                    "monitorado": "sim" if m.host_cmk else "nao",
                    "host_cmk": m.host_cmk or "",
                    "site": m.site_id or "",
                    "camada": m.camada,
                    "confianca": m.confianca,
                    "detalhe": m.detalhe,
                }
            )

    # hosts LEAF* que existem no Checkmk e não vieram de nenhum mapa ACI
    print("\nhosts LEAF* órfãos nos sites (sem leaf correspondente nos mapas):")
    orfaos = 0
    for sid, d in sorted(descobertos.items()):
        usados = usados_por_site.get(sid, set())
        for h in d.hosts_leaf:
            if h.upper() in usados or not normalizar_leaf(h):
                continue
            orfaos += 1
            print(f"  site {sid}: {h}")
            linhas.append(
                {
                    "fabric": "",
                    "leaf_aci": "",
                    "monitorado": "orfao-no-cmk",
                    "host_cmk": h,
                    "site": sid,
                    "camada": "-",
                    "confianca": "-",
                    "detalhe": "host LEAF* no Checkmk sem leaf no mapa ACI",
                }
            )
    if not orfaos:
        print("  nenhum")

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=list(linhas[0].keys()) if linhas else ["vazio"]
        )
        w.writeheader()
        w.writerows(linhas)
    print(f"\nconsolidado: {caminho.relative_to(RAIZ)}")
    nao_cobertos = sum(1 for x in linhas if x["monitorado"] == "nao")
    return 1 if nao_cobertos else 0


if __name__ == "__main__":
    raise SystemExit(main())

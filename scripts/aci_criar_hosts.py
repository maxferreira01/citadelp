#!/usr/bin/env python3
"""CITADEL · ACI — lista pronta de criação dos leafs sem monitoração no Checkmk.

Cruza a cobertura mais recente (scripts/aci_cobertura.py) com o APIC e o
Checkmk para montar, por leaf NAO-MONITORADO de site consultável, a linha
pronta de criação: site, host, IP OOB de gerência (topSystem do APIC) e o
folder onde os leafs já monitorados daquele site vivem. Tudo GET — a criação
em si é outro passo (POST /checkmk/{site}/hosts do citadelp, ou GUI).

Uso: python scripts/aci_criar_hosts.py                # todos os fabrics da cobertura
     python scripts/aci_criar_hosts.py --fabric TESP7 # um só
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.aci.client import AciClient, AciError
from app.aci.config import load_fabrics
from app.checkmk.gateway import CheckmkError, Gateway, load_sites

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


def ultima_cobertura() -> Path | None:
    arquivos = sorted((RAIZ / "relatorios" / "aci-portmap").glob("cobertura-*.csv"))
    return arquivos[-1] if arquivos else None


def ips_oob(client: AciClient) -> dict[str, str]:
    """name → oobMgmtAddr dos leafs do fabric (topSystem)."""
    out: dict[str, str] = {}
    for obj in client.get_all_pages("/api/node/class/topSystem.json"):
        at = obj.get("topSystem", {}).get("attributes", {})
        if at.get("role") != "leaf":
            continue
        ip = at.get("oobMgmtAddr", "")
        out[at.get("name", "").upper()] = "" if ip in ("", "0.0.0.0") else ip
    return out


def folder_dos_leafs(gw: Gateway) -> str:
    """Folder mais comum entre os hosts LEAF* já monitorados do site."""
    folders = Counter(
        h["folder"] for h in gw.list_hosts() if (h["id"] or "").upper().startswith("LEAF")
    )
    return folders.most_common(1)[0][0] if folders else "/"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fabric", help="um fabric só (default: todos da cobertura)")
    args = ap.parse_args()

    carregar_env()
    fabrics = load_fabrics()
    sites = load_sites()

    cobertura = ultima_cobertura()
    if cobertura is None:
        print("nenhuma cobertura-*.csv — rode scripts/aci_cobertura.py antes")
        return 2
    print(f"cobertura de referência: {cobertura.relative_to(RAIZ)}")

    faltantes: dict[str, list[str]] = {}
    for r in csv.DictReader(cobertura.open(encoding="utf-8")):
        fid = r["fabric"]
        if r["monitorado"] != "nao" or (args.fabric and fid != args.fabric):
            continue
        faltantes.setdefault(fid, []).append(r["leaf_aci"])

    ts = datetime.now(BRT).strftime("%Y%m%d-%H%M")
    caminho = RAIZ / "relatorios" / "aci-portmap" / f"criar-hosts-{ts}.csv"
    linhas: list[dict] = []
    sem_site: list[str] = []

    for fid in sorted(faltantes):
        fabric = fabrics.get(fid)
        if fabric is None:
            print(f"[{fid}] na cobertura mas fora de CITADEL_ACI_FABRICS — pulando")
            continue
        site = sites.get(fabric.cmk_site or "")
        if site is None:
            sem_site.append(fid)
            continue

        client = AciClient(fabric)
        try:
            ips = ips_oob(client)
        except AciError as exc:
            print(f"[{fid}] falha no APIC: {exc}")
            continue
        finally:
            client.close()

        try:
            folder = folder_dos_leafs(Gateway(site))
        except CheckmkError as exc:
            print(f"[{fid}] falha no site {site.id}: {exc} — usando folder /")
            folder = "/"

        print(f"\n[{fid}] {len(faltantes[fid])} leafs a criar no site {site.id} (folder {folder})")
        for leaf in sorted(faltantes[fid]):
            ip = ips.get(leaf.upper(), "")
            if not ip:
                print(f"  {leaf:<18} SEM IP OOB no APIC — completar antes de criar")
            linhas.append(
                {
                    "fabric": fid,
                    "site": site.id,
                    "host_name": leaf,
                    "ipaddress": ip,
                    "folder": folder,
                }
            )

    for fid in sem_site:
        print(
            f"\n[{fid}] site '{fabrics[fid].cmk_site}' sem automation user em "
            "CITADEL_CHECKMK_SITES — leafs fora da lista até haver credencial"
        )

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["fabric", "site", "host_name", "ipaddress", "folder"])
        w.writeheader()
        w.writerows(linhas)
    sem_ip = sum(1 for x in linhas if not x["ipaddress"])
    print(f"\n{len(linhas)} hosts na lista ({sem_ip} sem IP) → {caminho.relative_to(RAIZ)}")
    print("criação: POST /checkmk/{site}/hosts do citadelp (host + discovery + activate) ou GUI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""CITADEL · ACI — estágio 1: mapa de portas dos leafs, direto do APIC (GETs).

Varre um fabric (ou todos), classifica cada porta física de leaf (uplink de
fabric/APIC, NSX edge, firewall, SW de gerência, acesso a servidor, livre,
desconhecida) e grava os artefatos revisáveis em relatorios/aci-portmap/.
NADA é alterado em lugar nenhum — o silenciamento no Checkmk é outro estágio
(scripts/aci_silenciar.py), gated por --apply.

Uso: python scripts/aci_portmap.py --fabric TESP6      # um fabric
     python scripts/aci_portmap.py --fabric todos      # os 8
     python scripts/aci_portmap.py --fabric todos --probe   # só testa login
(lê CITADEL_ACI_FABRICS do ambiente; se ausente, carrega o .env da raiz)
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.aci.classificar import classificar_mapa
from app.aci.client import AciClient, AciError
from app.aci.coleta import coletar_fabric, coletar_nos
from app.aci.config import Fabric, load_fabrics


def carregar_env() -> None:
    """Carrega o .env da raiz quando a variável não veio do ambiente (padrão
    dos demais scripts: sem dependência de python-dotenv)."""
    if os.environ.get("CITADEL_ACI_FABRICS"):
        return
    env = RAIZ / ".env"
    if not env.is_file():
        return
    for linha in env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valor = valor.strip().strip("'\"")
        os.environ.setdefault(chave.strip(), valor)


def probe(fabric: Fabric) -> tuple[bool, str]:
    """Um login + uma listagem mínima. Em 401 NÃO insiste (risco de lockout)."""
    client = AciClient(fabric, timeout=15.0)
    try:
        nos = coletar_nos(client)
        papeis = Counter(n.role for n in nos)
        return True, (
            f"ok — {papeis.get('leaf', 0)} leafs, {papeis.get('spine', 0)} spines, "
            f"{papeis.get('controller', 0)} APICs"
        )
    except AciError as exc:
        return False, str(exc)
    finally:
        client.close()


def mapear(fabric: Fabric) -> int:
    from app.aci.artefatos import gravar_portmap

    mapa = coletar_fabric(fabric)
    mapeadas = classificar_mapa(mapa.portas, mapa.nos, fabric.padrao_nsx)
    paths = gravar_portmap(fabric.id, mapeadas)

    contagem = Counter(m.cls.classe.value for m in mapeadas)
    silenciar = sum(1 for m in mapeadas if m.cls.silenciar)
    print(f"\n[{fabric.id}] {len(mapa.leafs)} leafs, {len(mapa.portas)} portas físicas")
    for classe, n in contagem.most_common():
        print(f"  {classe:<16} {n}")
    print(
        f"  → candidatas a silenciar: {silenciar} | mantêm alarme: {len(mapeadas) - silenciar}"
    )
    print(f"  artefatos: {paths['csv'].relative_to(RAIZ)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fabric", required=True, help="id do fabric (ex. TESP6) ou 'todos'"
    )
    ap.add_argument(
        "--probe", action="store_true", help="só testa login/alcance, não mapeia"
    )
    args = ap.parse_args()

    carregar_env()
    fabrics = load_fabrics()
    if not fabrics:
        print("CITADEL_ACI_FABRICS vazio — configure o .env (ver .env.example)")
        return 2

    if args.fabric.lower() == "todos":
        alvos = list(fabrics.values())
    elif args.fabric in fabrics:
        alvos = [fabrics[args.fabric]]
    else:
        print(
            f"fabric '{args.fabric}' não registrado; existem: {', '.join(sorted(fabrics))}"
        )
        return 2

    falhas = 0
    for fabric in alvos:
        if args.probe:
            ok, msg = probe(fabric)
            print(f"[{fabric.id}] {msg}")
            falhas += 0 if ok else 1
        else:
            try:
                mapear(fabric)
            except AciError as exc:
                print(f"[{fabric.id}] FALHA: {exc}")
                falhas += 1
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())

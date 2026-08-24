#!/usr/bin/env python3
"""CITADEL · ACI — estágios 2 e 3: plano e aplicação do silenciamento no Checkmk.

Parte do último portmap do fabric (gerado por scripts/aci_portmap.py), descobre
onde os leafs vivem nos sites Checkmk, e:

  dry-run (default)  →  plano-regras-<ts>.json + divergencias-<ts>.csv, ZERO
                        escrita no Checkmk (as consultas são todas GET);
  --apply            →  substitui as regras CITADEL do fabric no site alvo
                        (remove antigas → cria novas → activate) e verifica;
  --verificar        →  só roda a verificação pós-apply (os dois lados).

Fail-safe em cada degrau: só entram portas classificadas como silenciáveis, só
leafs casados com confiança ALTA no site esperado; site Checkmk 1.5 (sem REST)
gera artefato manual-<site>.md em vez de mudança. --apply exige fabric
explícito — "todos" não aplica.

Uso: python scripts/aci_silenciar.py --fabric TESP6            # dry-run
     python scripts/aci_silenciar.py --fabric TESP6 --apply
     python scripts/aci_silenciar.py --fabric TESP6 --verificar
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.aci.artefatos import ultimo_portmap
from app.aci.cmk_match import MatchLeaf, casar_leafs, descobrir_sites
from app.aci.config import load_fabrics
from app.aci.regras import (
    CLASSES_MANTEM_ALARME,
    PlanoSite,
    aplicar_plano,
    conferir_servicos_existem,
    montar_plano,
    nome_servico,
    verificar_plano,
)
from app.checkmk.gateway import Gateway, load_sites

BRT = timezone(timedelta(hours=-3))


def carregar_env() -> None:
    env = RAIZ / ".env"
    if not env.is_file():
        return
    import os

    for linha in env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


def carregar_mapa(fabric_id: str) -> dict:
    caminho = ultimo_portmap(fabric_id)
    if caminho is None:
        raise SystemExit(
            f"nenhum portmap de {fabric_id} em relatorios/aci-portmap/ — "
            f"rode antes: python scripts/aci_portmap.py --fabric {fabric_id}"
        )
    print(f"mapa: {caminho.relative_to(RAIZ)}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_divergencias(
    destino: Path, ts: str, matches: list[MatchLeaf]
) -> Path | None:
    problemas = [
        m for m in matches if m.camada != "exato" or "COLISÃO" in (m.detalhe or "")
    ]
    if not problemas:
        return None
    caminho = destino / f"divergencias-{ts}.csv"
    with caminho.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["leaf_aci", "host_cmk", "site", "camada", "confianca", "detalhe"])
        for m in problemas:
            w.writerow(
                [
                    m.leaf_aci,
                    m.host_cmk or "",
                    m.site_id or "",
                    m.camada,
                    m.confianca,
                    m.detalhe,
                ]
            )
    return caminho


def gravar_manual(destino: Path, ts: str, site_id: str, plano: PlanoSite) -> Path:
    """Site 1.5 sem REST: a mesma mudança, como passo a passo para a GUI."""
    linhas = [
        f"# Silenciamento manual — site {site_id} (Checkmk 1.5, sem REST API)",
        "",
        (
            f"Gerado por scripts/aci_silenciar.py em {ts} a partir do portmap "
            f"do fabric {plano.fabric_id}. Aplicar em WATO: *Host & Service parameters →"
        ),
        "Monitoring configuration → Enable/disable notifications for services*,",
        'valor **disable** ("0"), uma regra por bloco abaixo:',
        "",
    ]
    for r in plano.regras:
        linhas += [f"## {r.description}", "", "Hosts:", ""]
        linhas += [f"- `{h}`" for h in r.hosts]
        linhas += ["", "Serviços (regex, âncora $ incluída):", ""]
        linhas += [f"- `{s}`" for s in r.servicos]
        linhas.append("")
    caminho = destino / f"manual-{site_id}-{ts}.md"
    caminho.write_text("\n".join(linhas), encoding="utf-8")
    return caminho


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fabric", required=True, help="id do fabric (ex. TESP6); 'todos' não aplica"
    )
    ap.add_argument(
        "--apply", action="store_true", help="efetiva as regras no site do fabric"
    )
    ap.add_argument("--verificar", action="store_true", help="só verificação pós-apply")
    args = ap.parse_args()

    if args.fabric.lower() == "todos":
        print(
            "--fabric todos não é aceito aqui: o rollout é site a site, com revisão entre eles"
        )
        return 2

    carregar_env()
    fabrics = load_fabrics()
    sites = load_sites()
    if args.fabric not in fabrics:
        print(
            f"fabric '{args.fabric}' não registrado; existem: {', '.join(sorted(fabrics))}"
        )
        return 2
    fabric = fabrics[args.fabric]
    if not fabric.cmk_site or fabric.cmk_site not in sites:
        print(
            f"cmk_site '{fabric.cmk_site}' do fabric {fabric.id} não está em "
            f"CITADEL_CHECKMK_SITES (sites: {', '.join(sorted(sites)) or 'nenhum'})"
        )
        return 2

    mapa = carregar_mapa(fabric.id)
    ts = datetime.now(BRT).strftime("%Y%m%d-%H%M")
    destino = RAIZ / "relatorios" / "aci-portmap" / fabric.id

    # --- descoberta e matching (tudo GET)
    descobertos = descobrir_sites(sites)
    for sid, d in sorted(descobertos.items()):
        rotulo = (
            "SEM REST (1.5)"
            if d.sem_rest
            else (d.erro or f"{d.versao} — {len(d.hosts_leaf)} leafs")
        )
        print(f"  site {sid}: {rotulo}")
    leafs_aci = sorted({p["leaf_name"] for p in mapa["portas"] if p["leaf_name"]})
    matches = casar_leafs(leafs_aci, descobertos, fabric.cmk_site)
    caminho_div = gravar_divergencias(destino, ts, matches)

    # só matches de confiança ALTA entram em regra; o resto é divergência
    host_por_leaf = {m.leaf_aci: m.host_cmk for m in matches if m.confianca == "alta"}
    excluidos = [m for m in matches if m.confianca != "alta"]

    portas_por_host: dict[str, list[str]] = {}
    mantem_alarme: dict[str, list[str]] = {}
    for p in mapa["portas"]:
        host = host_por_leaf.get(p["leaf_name"])
        if host is None:
            continue
        if p["silenciar"] == "sim":
            portas_por_host.setdefault(host, []).append(p["iface"])
        elif p["classe"] in {c.value for c in CLASSES_MANTEM_ALARME}:
            svc = nome_servico(p["iface"])
            if svc:
                mantem_alarme.setdefault(host, []).append(svc)

    plano = montar_plano(fabric.id, fabric.cmk_site, portas_por_host, ts)
    for m in excluidos:
        plano.avisos.append(f"fora do plano ({m.camada}): {m.leaf_aci} — {m.detalhe}")

    alvo = descobertos[fabric.cmk_site]
    if alvo.sem_rest:
        caminho_manual = gravar_manual(destino, ts, fabric.cmk_site, plano)
        print(
            f"\nsite {fabric.cmk_site} é 1.5 — artefato manual: {caminho_manual.relative_to(RAIZ)}"
        )
        return 0
    if alvo.erro:
        print(f"\nsite {fabric.cmk_site} inacessível: {alvo.erro}")
        return 1

    gw = Gateway(sites[fabric.cmk_site])
    try:
        if args.verificar:
            resultado = verificar_plano(gw, plano, mantem_alarme)
            print(json.dumps(resultado, ensure_ascii=False, indent=2))
            return 0 if resultado["ok"] else 1

        plano.avisos.extend(conferir_servicos_existem(gw, plano))

        caminho_plano = destino / f"plano-regras-{ts}.json"
        caminho_plano.write_text(
            json.dumps(
                {
                    "fabric": fabric.id,
                    "site": fabric.cmk_site,
                    "gerado_em": ts,
                    "regras": [r.payload() for r in plano.regras],
                    "avisos": plano.avisos,
                    "leafs_no_plano": sorted(portas_por_host),
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        print(
            f"\n[{fabric.id} → site {fabric.cmk_site}] {len(plano.regras)} regra(s), "
            f"{len(portas_por_host)} leaf(s), {plano.total_servicos} host×serviço"
        )
        for a in plano.avisos:
            print(f"  aviso: {a}")
        if caminho_div:
            print(f"  divergências: {caminho_div.relative_to(RAIZ)}")
        print(f"  plano: {caminho_plano.relative_to(RAIZ)}")

        if not args.apply:
            print("  (dry-run — nada foi alterado; use --apply para efetivar)")
            return 0

        recibo = aplicar_plano(gw, plano)
        print(f"  apply: {json.dumps(recibo, ensure_ascii=False)}")
        resultado = verificar_plano(gw, plano, mantem_alarme)
        print(f"  verificação: {json.dumps(resultado, ensure_ascii=False, indent=2)}")
        return 0 if recibo["ok"] and resultado["ok"] else 1
    finally:
        gw.close()


if __name__ == "__main__":
    raise SystemExit(main())

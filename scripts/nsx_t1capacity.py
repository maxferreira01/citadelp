#!/usr/bin/env python3
"""CITADEL · NSX — snapshot diário e validador da capacity de Tier-1.

Lê o InfluxDB central preenchido pelo nsx-collector e grava o snapshot em
relatorios/nsx-t1capacity/<SITE>/ (json = registro, csv = revisão, resumo =
site × t0/vrf × count/limit/pct). Não coleta nada em paralelo ao collector.

Uso: python scripts/nsx_t1capacity.py --site TESP6          # um site
     python scripts/nsx_t1capacity.py --site todos          # todos com dado
     python scripts/nsx_t1capacity.py --site todos --probe  # só testa acesso
     python scripts/nsx_t1capacity.py --site TESP6 --validar   # Manager × Influx (GET)
     python scripts/nsx_t1capacity.py --site TESP6 --com-edge  # + T1 por edge cluster
     python scripts/nsx_t1capacity.py --site TESP7 --criacao   # creation time de cada T1 (edge produtivo)

--validar refaz o cross-check: result_count da Manager × nsx_t1_totals.total ×
soma per_t0+per_vrf × capacity dashboard. Exit code = nº de sites divergentes
(tolerando criações/remoções dentro da janela de coleta via nsx_t1_event).
Somente GET no Manager; em 401/403 não insiste.

(lê CITADEL_INFLUX* / CITADEL_NSX_* do ambiente; se ausentes, carrega o .env
da raiz do repo)
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.nsx.artefatos import gravar_criacao, gravar_snapshot
from app.nsx.client import InfluxClient, NsxError
from app.nsx.config import (
    Manager,
    NsxConfigError,
    load_aliases,
    load_influx,
    load_managers,
)
from app.nsx.consultas import Consultas
from app.nsx.manager import ManagerClient, ManagerError
from app.nsx.modelos import T1PorEdge

TOLERANCIA_JANELA_MIN = 15  # 3 ciclos de capacity (intervals.slow = 5m)


def _rfc3339(txt: str) -> datetime:
    """Influx devolve nanossegundos; fromisoformat aceita até micro."""
    base, _, frac = txt.rstrip("Z").partition(".")
    return datetime.fromisoformat(f"{base}.{(frac + '000000')[:6]}").replace(
        tzinfo=timezone.utc
    )


def carregar_env() -> None:
    """Carrega o .env da raiz quando a variável não veio do ambiente (padrão
    dos demais scripts: sem dependência de python-dotenv)."""
    if os.environ.get("CITADEL_INFLUX"):
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


def probe_influx(q: Consultas) -> tuple[bool, str]:
    try:
        sites = q.resumo()
    except NsxError as exc:
        return False, str(exc)
    if not sites:
        return False, "Influx respondeu, mas sem nsx_t1_totals nos últimos 15 min"
    return True, "ok — " + ", ".join(f"{s.site}={s.total}" for s in sites)


def probe_manager(mgr: Manager) -> tuple[bool, str]:
    """Um GET mínimo. Em 401/403 NÃO insiste (risco de lockout)."""
    try:
        c = ManagerClient(mgr, timeout=20.0)
    except NsxConfigError as exc:
        return False, str(exc)
    try:
        return True, f"ok — result_count={c.total_tier1()}"
    except ManagerError as exc:
        return False, str(exc)
    finally:
        c.close()


def validar(q: Consultas, mgr: Manager, site: str) -> dict:
    """V4 automatizado: Manager × Influx, tolerando movimento na janela."""
    resumo = next((r for r in q.resumo(site) if r.site == site), None)
    por_t0, por_vrf = q.por_t0(site), q.por_vrf(site)
    soma = sum(t.t1_count for t in por_t0) + sum(v.t1_count for v in por_vrf)
    c = ManagerClient(mgr, timeout=30.0)
    try:
        mgr_total = c.total_tier1()
        cap = c.capacity_tier1()
    finally:
        c.close()
    # movimento recente: eventos created/deleted dentro da janela de tolerância
    limite = datetime.now(timezone.utc) - timedelta(minutes=TOLERANCIA_JANELA_MIN)
    recentes = [e for e in q.eventos(site, dias=1) if _rfc3339(e.quando) >= limite]
    tolerancia = max(1, len(recentes))
    influx_total = resumo.total if resumo else None
    influx_cap = resumo.nsx_current if resumo else None
    valores = {
        "manager_result_count": mgr_total,
        "manager_capacity_current": cap["current"],
        "manager_capacity_max": cap["max"],
        "influx_totals_total": influx_total,
        "influx_soma_per_t0_per_vrf": soma,
        "influx_capacity_current": influx_cap,
    }
    divergencias = []
    for nome, v in valores.items():
        if nome.startswith("manager_capacity_max") or v is None:
            if v is None:
                divergencias.append(f"{nome} ausente")
            continue
        if abs(v - mgr_total) > tolerancia:
            divergencias.append(
                f"{nome}={v} × manager={mgr_total} (tolerância {tolerancia})"
            )
    return {
        "site": site,
        "quando": datetime.now(timezone.utc).isoformat(),
        "valores": valores,
        "eventos_na_janela": len(recentes),
        "tolerancia": tolerancia,
        "ok": not divergencias,
        "divergencias": divergencias,
    }


def snapshot(
    q: Consultas, site: str, com_edge: bool, mgr: Manager | None, validacao: dict | None
) -> int:
    resumo = next((r for r in q.resumo(site) if r.site == site), None)
    por_t0, por_vrf = q.por_t0(site), q.por_vrf(site)
    por_edge: list[T1PorEdge] | None = None
    if com_edge:
        if mgr is None:
            print(
                f"[{site}] --com-edge exige o site em CITADEL_NSX_MANAGERS",
                file=sys.stderr,
            )
            return 1
        c = ManagerClient(mgr, timeout=120.0)
        try:
            por_edge = c.por_edge_cluster()
        finally:
            c.close()
    paths = gravar_snapshot(site, resumo, por_t0, por_vrf, por_edge, validacao)
    print(
        f"\n[{site}] T1 total={resumo.total if resumo else '?'} "
        f"(on_t0={resumo.on_t0 if resumo else '?'}, on_vrf={resumo.on_vrf if resumo else '?'}) "
        f"· NSX {resumo.nsx_current if resumo else '?'}/{resumo.nsx_max if resumo else '?'}"
    )
    for t in por_t0:
        print(
            f"  T0  {t.t0_name:<34} {t.t1_count:>5}/{t.limit:<5} {t.usage_pct:>6.1f}%"
        )
    for v in por_vrf:
        marca = " ◄" if v.usage_pct >= 90 else ""
        print(
            f"  VRF {v.vrf_name:<34} {v.t1_count:>5}/{v.limit:<5} {v.usage_pct:>6.1f}%{marca}"
        )
    for e in por_edge or []:
        print(f"  EDGE {e.edge_cluster_name:<33} {e.t1_count:>5}")
    if validacao:
        print(
            "  validação:",
            "OK"
            if validacao["ok"]
            else "DIVERGE — " + "; ".join(validacao["divergencias"]),
        )
    print("  →", paths["json"].relative_to(RAIZ))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--site", default="todos", help="site canônico (ex. TESP6) ou 'todos'"
    )
    ap.add_argument(
        "--probe",
        action="store_true",
        help="só testa Influx (e Managers, se --validar)",
    )
    ap.add_argument(
        "--validar", action="store_true", help="cross-check Manager × Influx (GET only)"
    )
    ap.add_argument(
        "--com-edge", action="store_true", help="agrega T1 por edge cluster via Manager"
    )
    ap.add_argument(
        "--criacao",
        action="store_true",
        help="grava snapshot com o _create_time de todos os T1 (Manager, GET) — edge produtivo",
    )
    args = ap.parse_args()

    carregar_env()
    try:
        q = Consultas(InfluxClient(load_influx()), load_aliases())
        managers = load_managers()
    except NsxConfigError as exc:
        print(f"config: {exc}", file=sys.stderr)
        return 2

    falhas = 0
    if args.probe:
        ok, msg = probe_influx(q)
        print(f"influx: {msg}")
        falhas += 0 if ok else 1
        if args.validar or args.com_edge:
            alvos = (
                managers.values()
                if args.site == "todos"
                else [m for m in managers.values() if m.id == args.site]
            )
            for m in alvos:
                ok, msg = probe_manager(m)
                print(f"manager {m.id}: {msg}")
                falhas += 0 if ok else 1
        return falhas

    if args.site == "todos":
        sites = [r.site for r in q.resumo()]
    else:
        sites = [args.site]
    for site in sites:
        mgr = managers.get(site)
        validacao = None
        try:
            if args.validar:
                if mgr is None:
                    print(
                        f"[{site}] --validar: site sem Manager em CITADEL_NSX_MANAGERS, pulando validação"
                    )
                else:
                    validacao = validar(q, mgr, site)
                    if not validacao["ok"]:
                        falhas += 1
            falhas += snapshot(q, site, args.com_edge, mgr, validacao)
            if args.criacao:
                if mgr is None:
                    print(
                        f"[{site}] --criacao exige o site em CITADEL_NSX_MANAGERS",
                        file=sys.stderr,
                    )
                    falhas += 1
                else:
                    c = ManagerClient(mgr, timeout=120.0)
                    try:
                        itens = c.tier1_criacao()
                    finally:
                        c.close()
                    caminho = gravar_criacao(site, itens)
                    print(
                        f"  criação: {len(itens)} T1 com _create_time → {caminho.relative_to(RAIZ)}"
                    )
        except (NsxError, ManagerError, NsxConfigError) as exc:
            print(f"[{site}] {exc}", file=sys.stderr)
            falhas += 1
    return falhas


if __name__ == "__main__":
    sys.exit(main())

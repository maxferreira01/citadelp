#!/usr/bin/env python3
"""Relatório de consumo dos firewalls (Palo Alto) via CITADEL·CORVO.

Lida com os dois modelos do site: nós standalone (serviços "CPU utilization",
"Memory", "Palo Alto Sessions" sem sufixo) e clusters HA (um host-objeto carrega
os serviços de cada membro com sufixo, ex.: "CPU utilization FW02TBCE01", mais um
agregado sem sufixo). Emite uma linha por firewall físico — ativo E passivo —
deduplicando membros que se repetem entre host-objetos. Somente leitura.

Uso: python scripts/fw_consumo.py            (lê CITADEL_CHECKMK_SITES do .env)
     python scripts/fw_consumo.py --json
"""

from __future__ import annotations

import json
import os
import sys

import httpx

BASES = ("CPU utilization", "Memory", "Palo Alto Sessions", "Sessions")


def first_val(perf: str, *names: str) -> float | None:
    fields = {}
    for tok in perf.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            try:
                fields[k] = float(v.split(";")[0])
            except ValueError:
                pass
    for n in names:
        if n in fields:
            return fields[n]
    return None


def classify(desc: str) -> tuple[str, str | None] | None:
    """(base, suffix) — suffix=None quando o serviço é do próprio host."""
    for b in BASES:
        if desc == b:
            return b, None
        if desc.startswith(b + " "):
            return b, desc[len(b) + 1 :]
    return None


def main() -> int:
    as_json = "--json" in sys.argv
    s = json.loads(os.environ["CITADEL_CHECKMK_SITES"])[0]
    base_url = s["url"].rstrip("/") + "/check_mk/api/1.0"
    c = httpx.Client(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {s['user']} {s['secret']}",
            "Accept": "application/json",
        },
        timeout=30,
    )

    fw_hosts = [
        h["id"]
        for h in c.get("/domain-types/host_config/collections/all").json()["value"]
        if "fw" in h["id"].lower()
    ]

    members: dict[str, dict] = {}  # nome do firmware físico -> métricas
    sem_dados: list[str] = []

    for host in sorted(fw_hosts):
        svcs = c.get(
            "/domain-types/service/collections/all",
            params=[
                ("host_name", host),
                ("columns", "description"),
                ("columns", "perf_data"),
            ],
        ).json()["value"]

        parsed = []
        for sv in svcs:
            d = sv["extensions"].get("description", "")
            cl = classify(d)
            if cl:
                parsed.append((cl[0], cl[1], sv["extensions"].get("perf_data", "")))

        suffixes = {suf for _, suf, _ in parsed if suf}
        # cluster: usa membros com sufixo; standalone: usa o próprio host.
        # Caso FW04TESP05: o host-objeto traz só o PAR com sufixo e os dados
        # dele mesmo sem sufixo — inclui o host como membro também.
        targets = set(suffixes) if suffixes else {host}
        if len(suffixes) == 1 and host not in suffixes:
            targets.add(host)
        # serviços com sufixo têm precedência sobre o agregado sem sufixo
        parsed.sort(key=lambda t: t[1] is None)

        for member in targets:
            row = members.setdefault(
                member, {"cpu": None, "mem": None, "ses": None, "via": host}
            )
            for b, suf, perf in parsed:
                # sufixo casa com o membro; sem sufixo casa com o próprio host
                if not (suf == member or (suf is None and member == host)):
                    continue
                if b == "CPU utilization" and row["cpu"] is None:
                    row["cpu"] = first_val(perf, "util")
                elif b == "Memory" and row["mem"] is None:
                    row["mem"] = first_val(perf, "mem_used_percent")
                elif b in ("Sessions", "Palo Alto Sessions") and row["ses"] is None:
                    row["ses"] = first_val(perf, "total_active_sessions", "session")

        if not parsed:
            sem_dados.append(host)

    rows = [{"firewall": m, **v} for m, v in members.items()]
    rows.sort(key=lambda x: (x["cpu"] is None, -(x["cpu"] or 0)))

    if as_json:
        print(json.dumps({"firewalls": rows, "sem_coleta": sem_dados}, indent=2))
        return 0

    print(f"{'FIREWALL':16} {'CPU%':>6} {'MEM%':>6} {'SESSÕES':>12}")
    print("-" * 44)
    for x in rows:
        cpu = f"{x['cpu']:.1f}" if x["cpu"] is not None else "-"
        mem = f"{x['mem']:.1f}" if x["mem"] is not None else "-"
        ses = f"{int(x['ses']):,}" if x["ses"] is not None else "-"
        flag = "  <== CPU>=80" if (x["cpu"] or 0) >= 80 else ""
        print(f"{x['firewall']:16} {cpu:>6} {mem:>6} {ses:>12}{flag}")
    print(f"\ntotal firewalls: {len(rows)}")
    if sem_dados:
        print(f"sem coleta (só Check_MK/CRIT): {', '.join(sem_dados)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Banda das interfaces dos firewalls via web API legada (get_graph).

Fallback para sites Checkmk 2.1 sem Livestatus TCP (ex.: mk_tesp5): a web API
(reabilitada na GUI) entrega as séries dos gráficos. Curvas "Input/Output
bandwidth" vêm em bits/s (out pode vir negativo — espelho do gráfico; usamos
o módulo). O passo é escolhido pelo Checkmk conforme a janela.

Uso: CITADEL_CHECKMK_SITES=... python scripts/fw_banda_webapi.py <site_id> <dias> [--csv out.csv]
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx


def main() -> int:
    site_id, days = sys.argv[1], int(sys.argv[2])
    csv_path = sys.argv[sys.argv.index("--csv") + 1] if "--csv" in sys.argv else None

    site = next(
        s for s in json.loads(os.environ["CITADEL_CHECKMK_SITES"]) if s["id"] == site_id
    )
    root = site["url"].rstrip("/")
    rest = httpx.Client(
        base_url=root + "/check_mk/api/1.0",
        headers={
            "Authorization": f"Bearer {site['user']} {site['secret']}",
            "Accept": "application/json",
        },
        timeout=60,
    )
    end = int(time.time())
    start = end - days * 86400

    fw_hosts = sorted(
        h["id"]
        for h in rest.get("/domain-types/host_config/collections/all").json()["value"]
        if "fw" in h["id"].lower()
    )

    # setups distribuídos: o gráfico mora no site que monitora o host
    host_site: dict[str, str] = {}
    for host in fw_hosts:
        eff = rest.get(
            f"/objects/host_config/{host}", params={"effective_attributes": "true"}
        ).json()
        attrs = eff.get("extensions", {})
        host_site[host] = (
            attrs.get("effective_attributes") or attrs.get("attributes", {})
        ).get("site") or site_id

    jobs = []  # (host, iface, speed_mbps, service_description)
    for host in fw_hosts:
        svcs = rest.get(
            "/domain-types/service/collections/all",
            params=[
                ("host_name", host),
                ("columns", "description"),
                ("columns", "perf_data"),
            ],
        ).json()["value"]
        for sv in svcs:
            d = sv["extensions"]["description"]
            if not d.startswith("Interface "):
                continue
            speed = None
            for tok in sv["extensions"].get("perf_data", "").split():
                if tok.startswith("in="):
                    parts = tok.split("=")[1].split(";")
                    if len(parts) >= 5 and parts[4]:
                        speed = float(parts[4]) * 8 / 1e6
            jobs.append((host, d[len("Interface ") :], speed, d))

    print(
        f"{len(fw_hosts)} firewalls, {len(jobs)} interfaces — coletando "
        f"{days}d via get_graph...",
        file=sys.stderr,
    )

    def fetch(job):
        host, iface, speed, svc = job
        try:
            r = httpx.post(
                f"{root}/check_mk/webapi.py",
                params={
                    "action": "get_graph",
                    "_username": site["user"],
                    "_secret": site["secret"],
                },
                data={
                    "request": json.dumps(
                        {
                            "specification": [
                                "template",
                                {
                                    "site": host_site.get(host, site_id),
                                    "host_name": host,
                                    "service_description": svc,
                                    "graph_index": 0,
                                },
                            ],
                            "data_range": {"time_range": [start, end]},
                        }
                    )
                },
                timeout=60,
            ).json()
        except (httpx.HTTPError, ValueError):
            return None
        if r.get("result_code") != 0:
            return None
        stats = {}
        for curve in r["result"].get("curves", []):
            title = curve.get("title", "").lower()
            key = "in" if "input" in title else "out" if "output" in title else None
            if not key:
                continue
            vals = [abs(v) for v in curve.get("rrddata", []) if v is not None]
            if vals:
                stats[key] = (sum(vals) / len(vals) / 1e6, max(vals) / 1e6)
        peak = max((s[1] for s in stats.values()), default=None)
        return {
            "firewall": host,
            "interface": iface,
            "speed_mbps": speed,
            "avg_in_mbps": stats.get("in", (None,))[0],
            "max_in_mbps": stats.get("in", (None, None))[1],
            "avg_out_mbps": stats.get("out", (None,))[0],
            "max_out_mbps": stats.get("out", (None, None))[1],
            "util_pico_pct": (peak / speed * 100) if speed and peak else None,
        }

    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = [r for r in ex.map(fetch, jobs) if r]

    rows.sort(key=lambda x: -max(x["max_in_mbps"] or 0, x["max_out_mbps"] or 0))
    if csv_path:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    ok_in = sum(1 for x in rows if x["max_in_mbps"] is not None)
    print(
        f"coletadas {len(rows)} interfaces ({ok_in} com série) de {len(jobs)} tentadas",
        file=sys.stderr,
    )
    for x in rows[:15]:
        print(
            f"{x['firewall']:14} {x['interface']:18} "
            f"maxIn={x['max_in_mbps'] or 0:8.0f} maxOut={x['max_out_mbps'] or 0:8.0f} Mbps"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

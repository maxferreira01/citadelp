#!/usr/bin/env python3
"""Banda das interfaces dos firewalls via REST metric API (Checkmk 2.3+).

Terceiro caminho de coleta do módulo CORVO, para sites onde a API de métricas
do REST existe (2.3+) — mais limpa que a web API legada e sem depender de
Livestatus TCP. Métricas ``if_in_bps``/``if_out_bps`` já vêm em bits/s.

Faz uma passada com ``reduce=max`` (pico) e, só nas interfaces que tiveram
tráfego, uma segunda com ``reduce=average`` — evita milhares de chamadas em
interfaces ociosas.

Uso: CITADEL_CHECKMK_SITES=... python scripts/fw_banda_rest.py <site_id> <dias> [--csv out.csv]
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx

MIN_TRAFEGO_MBPS = 0.1  # abaixo disso não vale a chamada de média


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    site_id, days = sys.argv[1], int(sys.argv[2])
    csv_path = sys.argv[sys.argv.index("--csv") + 1] if "--csv" in sys.argv else None

    site = next(
        s for s in json.loads(os.environ["CITADEL_CHECKMK_SITES"]) if s["id"] == site_id
    )
    base = site["url"].rstrip("/") + "/check_mk/api/1.0"
    headers = {
        "Authorization": f"Bearer {site['user']} {site['secret']}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    rest = httpx.Client(base_url=base, headers=headers, timeout=60)

    end = time.time()
    start = end - days * 86400
    tr = {"start": iso(start), "end": iso(end)}

    fw_hosts = sorted(
        h["id"]
        for h in rest.get("/domain-types/host_config/collections/all").json()["value"]
        if "fw" in h["id"].lower()
    )

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
        f"{len(fw_hosts)} firewalls, {len(jobs)} interfaces — coletando {days}d "
        f"via REST metric API...",
        file=sys.stderr,
    )

    def serie(host: str, svc: str, metric: str, reduce: str) -> float | None:
        """Retorna o valor consolidado (máx da série) em Mbps, ou None."""
        try:
            r = httpx.post(
                f"{base}/domain-types/metric/actions/get/invoke",
                headers=headers,
                json={
                    "type": "single_metric",
                    "host_name": host,
                    "service_description": svc,
                    "metric_id": metric,
                    "time_range": tr,
                    "reduce": reduce,
                },
                timeout=60,
            )
            if r.status_code != 200:
                return None
            pts = [
                v
                for m in r.json().get("metrics", [])
                for v in m.get("data_points", [])
                if v is not None
            ]
        except (httpx.HTTPError, ValueError):
            return None
        if not pts:
            return None
        vals = [abs(v) / 1e6 for v in pts]
        return max(vals) if reduce == "max" else sum(vals) / len(vals)

    def fetch(job):
        host, iface, speed, svc = job
        max_in = serie(host, svc, "if_in_bps", "max")
        max_out = serie(host, svc, "if_out_bps", "max")
        peak = max((v for v in (max_in, max_out) if v is not None), default=None)
        avg_in = avg_out = None
        if peak and peak >= MIN_TRAFEGO_MBPS:
            avg_in = serie(host, svc, "if_in_bps", "average")
            avg_out = serie(host, svc, "if_out_bps", "average")
        return {
            "firewall": host,
            "interface": iface,
            "speed_mbps": speed,
            "avg_in_mbps": avg_in,
            "max_in_mbps": max_in,
            "avg_out_mbps": avg_out,
            "max_out_mbps": max_out,
            "util_pico_pct": (peak / speed * 100) if speed and peak else None,
        }

    with ThreadPoolExecutor(max_workers=10) as ex:
        rows = [r for r in ex.map(fetch, jobs) if r]

    rows.sort(key=lambda x: -max(x["max_in_mbps"] or 0, x["max_out_mbps"] or 0))
    if csv_path and rows:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    com_serie = sum(1 for x in rows if x["max_in_mbps"] is not None)
    print(
        f"coletadas {len(rows)} interfaces ({com_serie} com série) de {len(jobs)}",
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

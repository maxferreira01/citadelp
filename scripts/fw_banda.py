#!/usr/bin/env python3
"""Relatório de banda das interfaces dos firewalls — 7 dias via Livestatus/RRD.

Fonte: Livestatus TLS (porta 6557) do site central, colunas rrddata (RRA de 1h).
O transporte usa openssl s_client porque o ssl do Python não suporta o
half-close que o Livestatus exige. Valores dos RRDs em bytes/s → saída em Mbps.

Uso: python scripts/fw_banda.py <dias> [--csv saida.csv] [--json]
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time

HOST, PORT = "10.114.35.180", 6557
STEP = 3600  # RRA horária


def lsq(lql: str) -> list:
    r = subprocess.run(
        ["openssl", "s_client", "-connect", f"{HOST}:{PORT}", "-quiet"],
        input=(lql + "\n\n").encode(),
        capture_output=True,
        timeout=120,
        check=False,
    )
    out = r.stdout.decode(errors="replace").strip()
    if not out:
        raise RuntimeError(f"Livestatus sem resposta: {r.stderr.decode()[:200]}")
    return json.loads(out)


def series_stats(rrd: list) -> tuple[float, float] | None:
    """rrd = [start, end, step, v...] em bytes/s → (avg_mbps, max_mbps)."""
    vals = [v for v in rrd[3:] if v is not None]
    if not vals:
        return None
    to_mbps = 8 / 1e6
    return (sum(vals) / len(vals) * to_mbps, max(vals) * to_mbps)


def main() -> int:
    days = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 7
    csv_path = None
    if "--csv" in sys.argv:
        csv_path = sys.argv[sys.argv.index("--csv") + 1]
    as_json = "--json" in sys.argv

    end = int(time.time())
    start = end - days * 86400

    rows_raw = lsq(
        "GET services\n"
        "Columns: host_name description"
        f" rrddata:ia:in.average:{start}:{end}:{STEP}"
        f" rrddata:im:in.max:{start}:{end}:{STEP}"
        f" rrddata:oa:out.average:{start}:{end}:{STEP}"
        f" rrddata:om:out.max:{start}:{end}:{STEP}"
        " perf_data\n"
        "Filter: host_name ~~ ^fw\n"
        "Filter: description ~ ^Interface \n"
        "OutputFormat: json"
    )

    ifaces = []
    for hn, desc, ia, im, oa, om, perf in rows_raw:
        name = desc[len("Interface ") :]
        speed_bps = None
        for tok in perf.split():
            if tok.startswith("in="):
                parts = tok.split("=")[1].split(";")
                if len(parts) >= 5 and parts[4]:
                    speed_bps = float(parts[4])
        s_ia, s_im = series_stats(ia) or (None, None), series_stats(im) or (None, None)
        s_oa, s_om = series_stats(oa) or (None, None), series_stats(om) or (None, None)
        speed_mbps = speed_bps * 8 / 1e6 if speed_bps else None
        max_in = s_im[1] if s_im[1] is not None else None
        max_out = s_om[1] if s_om[1] is not None else None
        peak = max(x for x in (max_in, max_out, 0.0) if x is not None)
        ifaces.append(
            {
                "firewall": hn,
                "interface": name,
                "speed_mbps": speed_mbps,
                "avg_in_mbps": s_ia[0],
                "max_in_mbps": max_in,
                "avg_out_mbps": s_oa[0],
                "max_out_mbps": max_out,
                "util_pico_pct": (peak / speed_mbps * 100)
                if speed_mbps and peak
                else None,
            }
        )

    ifaces.sort(key=lambda x: -(max(x["max_in_mbps"] or 0, x["max_out_mbps"] or 0)))

    if csv_path:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(ifaces[0].keys()))
            w.writeheader()
            w.writerows(ifaces)

    if as_json:
        print(json.dumps({"dias": days, "interfaces": ifaces}, indent=2))
        return 0

    print(f"BANDA — últimos {days} dias · RRA 1h · valores em Mbps")
    print(
        f"{'FIREWALL':12} {'INTERFACE':16} {'SPEED':>7} {'AVG IN':>9} {'MAX IN':>9} "
        f"{'AVG OUT':>9} {'MAX OUT':>9} {'PICO%':>6}"
    )
    print("-" * 84)
    shown = 0
    for x in ifaces:
        if (x["max_in_mbps"] or 0) < 1 and (x["max_out_mbps"] or 0) < 1:
            continue  # tabela: só interfaces com tráfego; CSV/JSON têm todas
        fmt = lambda v: f"{v:.0f}" if v is not None else "-"
        print(
            f"{x['firewall']:12} {x['interface']:16} {fmt(x['speed_mbps']):>7} "
            f"{fmt(x['avg_in_mbps']):>9} {fmt(x['max_in_mbps']):>9} "
            f"{fmt(x['avg_out_mbps']):>9} {fmt(x['max_out_mbps']):>9} "
            f"{fmt(x['util_pico_pct']):>6}"
        )
        shown += 1
    print(
        f"\ninterfaces com tráfego: {shown} · total mapeadas: {len(ifaces)}"
        + (f" · CSV completo: {csv_path}" if csv_path else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

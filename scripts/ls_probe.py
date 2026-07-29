#!/usr/bin/env python3
"""Teste de Livestatus rrddata p/ histórico de banda (7 dias)."""

import json
import subprocess
import sys

HOST, PORT = "10.114.35.180", 6557


def q(lql: str) -> str:
    """Livestatus sobre TLS. openssl s_client resolve o half-close que o
    ssl do Python não suporta; CA interna do site — validar cert depois."""
    r = subprocess.run(
        ["openssl", "s_client", "-connect", f"{HOST}:{PORT}", "-quiet"],
        input=(lql + "\n").encode(),
        capture_output=True,
        timeout=30,
        check=False,
    )
    return r.stdout.decode(errors="replace")


# 1) sanity: o Livestatus responde?
print("== status central:")
print(q("GET status\nColumns: livestatus_version program_version\nOutputFormat: json"))

# 2) rrddata de uma interface (7 dias). Janela passada via argv (epoch start end).
start, end = int(sys.argv[1]), int(sys.argv[2])
step = 3600  # 1h
host = "FW01TESP02"
svc = "Interface ethernet1/14"
for var in ("in", "out"):
    lql = (
        "GET services\n"
        f"Columns: rrddata:{var}:{var}.max:{start}:{end}:{step}\n"
        f"Filter: host_name = {host}\n"
        f"Filter: description = {svc}\n"
        "OutputFormat: json"
    )
    print(f"\n== rrddata {var} ({host} / {svc}):")
    out = q(lql)
    try:
        data = json.loads(out)[0][0]  # [start, end, step, v1, v2, ...]
        vals = [v for v in data[3:] if v is not None]
        if vals:
            print(
                f"  pontos={len(data[3:])} validos={len(vals)} "
                f"max={max(vals) / 1e6:.1f} MB/s avg={sum(vals) / len(vals) / 1e6:.1f} MB/s"
            )
        else:
            print("  sem pontos válidos:", data[:6])
    except (ValueError, IndexError, TypeError) as e:
        print("  erro:", e, "| resposta:", out[:200])

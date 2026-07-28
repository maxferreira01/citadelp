"""Corvo — parsing dos alertas do bot Alert Float IP (regras validadas na varredura real)."""

from __future__ import annotations

import re

FIELD_RES = {
    "edge": re.compile(r"\*Edge:\*\s*([A-Z0-9]+)", re.I),
    "cluster": re.compile(r"\*Cluster:\*\s*([\w]+)", re.I),
    "success": re.compile(r"\*Sucesso:\*\s*([\d.,]+)", re.I),
    "failure": re.compile(r"\*Falha:\*\s*([\d.,]+)", re.I),
    "high_latency": re.compile(r"\*Alta\s+Lat[êe]ncia:\*\s*([\d.,]+)", re.I),
}
PACKET_LOSS_RE = re.compile(r"perda\s+de\s+pacote", re.I)


def parse_attachment(blob: str) -> dict | None:
    """Extrai edge/cluster/contagens do attachment; None se não for alerta completo."""
    fields: dict[str, str] = {}
    for key, rx in FIELD_RES.items():
        m = rx.search(blob)
        if m:
            fields[key] = m.group(1)
    if not {"edge", "success", "failure", "high_latency"} <= fields.keys():
        return None
    s, f, hl = (
        int(fields[k].replace(".", "").replace(",", ""))
        for k in ("success", "failure", "high_latency")
    )
    total = max(s + f + hl, 1)
    degraded = round(100 * (f + hl) / total, 1)
    pl = bool(PACKET_LOSS_RE.search(blob))
    severity = "emergency" if pl or degraded >= 30 else "crit" if degraded >= 15 else "warn"
    return {
        "edge": fields["edge"].upper(),
        "cluster": fields.get("cluster", "?").replace("Cluster_", ""),
        "success": s,
        "failure": f,
        "high_latency": hl,
        "packet_loss": pl,
        "degraded_pct": degraded,
        "severity": severity,
    }

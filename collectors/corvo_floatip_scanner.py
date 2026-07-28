#!/usr/bin/env python3
"""CITADEL · CORVO — coletor do canal #alert-float-ip (C05JX7J5MMY).

Escaneia o histórico do canal via Slack Web API, parseia os alertas do bot
"Alert Float IP" (attachments com Edge/Cluster/Sucesso/Falha/Alta Latência),
captura as atuações humanas e emite um JSON consumido pelo módulo
corvo_raiox_floatip.jsx (substituindo o dataset embutido no protótipo).

Uso:
    export SLACK_BOT_TOKEN=xoxb-...   # escopos: channels:history, reactions:read, files:read
    python corvo_floatip_scanner.py --days 90 --out data/floatip_scan.json

Decisões (validadas na varredura manual de 27 jul 2026):
- O bot posta 2 mensagens por alerta (attachment + arquivo .log): deduplicamos
  por (edge, cluster, janela de 120 s).
- Reações são proxy de ack: eyes=visto, white_check_mark=tratado. O ts da
  reação NÃO vem no history — buscamos via reactions.get para calcular MTTA real.
- Severidade v1: ratio = (falha + alta_lat) / total.
  >=30% ou "perda de pacote" no título => emergency; >=15% => crit; senão warn.
- Storm: >=3 alertas do mesmo edge em <=120 s.
- Silenciamento: alertas dentro de janela de RDM (integração futura c/ ServiceNow)
  são marcados expected=True em vez de descartados — auditoria de schedule.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta

CHANNEL_ID = "C05JX7J5MMY"
BOT_USER = "U05JGPLN8UX"          # Alert Float IP
API = "https://slack.com/api"
BRT = timezone(timedelta(hours=-3))

# "Diversos IPs de float do Cluster_2_TESP3 apresentando alta latência [e perda de pacote]"
# Janelas de manutenção conhecidas (MAN — origem: relato humano no canal).
# Ao integrar com ServiceNow, substituir por consulta às RDMs aprovadas.
EXPECTED_WINDOWS = [
    # (início BRT, fim BRT, edge ou None=todos, motivo)
    ("2026-05-24T23:00", "2026-05-25T01:00", "TECE",  "RDM 549523 · TETRIS/AMD — schedule de silêncio falhou"),
    ("2026-06-21T23:00", "2026-06-22T01:00", "TESP3", "Manutenção NSX · limpeza de disco no Cluster 2"),
]

TITLE_RE = re.compile(r"Cluster[_\s]?(?P<cluster>\d+)[_\s]?(?P<edge>T[A-Z]{3}\d+)", re.I)
FIELD_RES = {
    "edge": re.compile(r"\*Edge:\*\s*([A-Z0-9]+)", re.I),
    "cluster": re.compile(r"\*Cluster:\*\s*([\w]+)", re.I),
    "success": re.compile(r"\*Sucesso:\*\s*([\d.,]+)", re.I),
    "failure": re.compile(r"\*Falha:\*\s*([\d.,]+)", re.I),
    "high_latency": re.compile(r"\*Alta\s+Lat[êe]ncia:\*\s*([\d.,]+)", re.I),
}
PACKET_LOSS_RE = re.compile(r"perda\s+de\s+pacote", re.I)


@dataclass
class Alert:
    ts: str
    iso: str
    edge: str
    cluster: str
    success: int
    failure: int
    high_latency: int
    packet_loss: bool
    severity: str = "warn"
    degraded_pct: float = 0.0
    seen: bool = False            # reação :eyes:
    done: bool = False            # reação :white_check_mark:
    ack_seconds: int | None = None  # ts da 1ª reação - ts do alerta (MTTA real)
    replies: int = 0
    log_file_id: str | None = None
    storm_id: str | None = None
    expected: bool = False        # dentro de janela de RDM (futuro)


@dataclass
class HumanAction:
    ts: str
    iso: str
    user: str
    text: str


def _call(method: str, token: str, **params) -> dict:
    url = f"{API}/{method}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if not data.get("ok"):
        raise RuntimeError(f"{method}: {data.get('error')}")
    return data


def fetch_history(token: str, oldest: float) -> list[dict]:
    msgs, cursor = [], None
    while True:
        kw = {"channel": CHANNEL_ID, "limit": 200, "oldest": f"{oldest:.6f}"}
        if cursor:
            kw["cursor"] = cursor
        data = _call("conversations.history", token, **kw)
        msgs.extend(data.get("messages", []))
        cursor = (data.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(1.1)  # tier 3 rate limit
    return msgs


def parse_alert(msg: dict) -> Alert | None:
    if msg.get("user") != BOT_USER and msg.get("bot_id") is None:
        return None
    blob = json.dumps(msg.get("attachments", []), ensure_ascii=False)
    if "Edge" not in blob:
        return None
    fields = {}
    for key, rx in FIELD_RES.items():
        m = rx.search(blob)
        if m:
            fields[key] = m.group(1)
    if not {"edge", "success", "failure", "high_latency"} <= fields.keys():
        return None  # mensagem-irmã só com o .log, ou payload incompleto
    ts = msg["ts"]
    dt = datetime.fromtimestamp(float(ts), BRT)
    s, f, hl = (int(fields[k].replace(".", "").replace(",", "")) for k in ("success", "failure", "high_latency"))
    a = Alert(
        ts=ts,
        iso=dt.isoformat(),
        edge=fields["edge"].upper(),
        cluster=fields.get("cluster", "?").replace("Cluster_", ""),
        success=s, failure=f, high_latency=hl,
        packet_loss=bool(PACKET_LOSS_RE.search(blob)),
        replies=int(msg.get("reply_count", 0)),
    )
    total = max(s + f + hl, 1)
    a.degraded_pct = round(100 * (f + hl) / total, 1)
    a.severity = ("emergency" if a.packet_loss or a.degraded_pct >= 30
                  else "crit" if a.degraded_pct >= 15 else "warn")
    for r in msg.get("reactions", []):
        if r["name"] == "eyes":
            a.seen = True
        if r["name"] == "white_check_mark":
            a.done = True
    return a


def attach_logs(alerts: list[Alert], msgs: list[dict]) -> None:
    """Associa o .log postado pelo bot logo após cada alerta (dedup 120 s)."""
    files = [(float(m["ts"]), m["files"][0]["id"]) for m in msgs
             if m.get("files") and (m.get("user") == BOT_USER or m.get("bot_id"))]
    for a in alerts:
        t = float(a.ts)
        for fts, fid in files:
            if 0 <= fts - t <= 120:
                a.log_file_id = fid
                break


def mark_expected(alerts: list[Alert]) -> None:
    for a in alerts:
        dt = datetime.fromtimestamp(float(a.ts), BRT).replace(tzinfo=None)
        for start, end, edge, _reason in EXPECTED_WINDOWS:
            if edge and a.edge != edge:
                continue
            if datetime.fromisoformat(start) <= dt <= datetime.fromisoformat(end):
                a.expected = True
                break


def tag_storms(alerts: list[Alert]) -> None:
    by_edge: dict[str, list[Alert]] = defaultdict(list)
    for a in sorted(alerts, key=lambda x: float(x.ts)):
        by_edge[a.edge].append(a)
    for edge, seq in by_edge.items():
        run: list[Alert] = []
        for a in seq:
            if run and float(a.ts) - float(run[-1].ts) <= 120:
                run.append(a)
            else:
                if len(run) >= 3:
                    sid = f"storm-{edge}-{run[0].iso[:16]}"
                    for x in run:
                        x.storm_id = sid
                run = [a]
        if len(run) >= 3:
            sid = f"storm-{edge}-{run[0].iso[:16]}"
            for x in run:
                x.storm_id = sid


def fetch_ack_times(token: str, alerts: list[Alert]) -> None:
    """MTTA real: reactions.get não traz ts da reação; aproximamos pelo 1º reply
    humano na thread (conversations.replies) — documentado como proxy."""
    for a in alerts:
        if a.replies <= 1:
            continue
        try:
            data = _call("conversations.replies", token, channel=CHANNEL_ID, ts=a.ts, limit=10)
        except RuntimeError:
            continue
        for m in data.get("messages", [])[1:]:
            if m.get("user") and m["user"] != BOT_USER:
                a.ack_seconds = int(float(m["ts"]) - float(a.ts))
                break
        time.sleep(1.1)


def summarize(alerts: list[Alert], actions: list[HumanAction]) -> dict:
    tot = len(alerts) or 1
    by_ec = defaultdict(int)
    by_ec_actionable = defaultdict(int)   # expurgando janelas de manutenção
    for a in alerts:
        key = f"{a.edge} C{a.cluster}"
        by_ec[key] += 1
        if not a.expected:
            by_ec_actionable[key] += 1
    night = sum(1 for a in alerts if int(a.iso[11:13]) < 6)
    acked = [a.ack_seconds for a in alerts if a.ack_seconds is not None]
    return {
        "total_alerts": len(alerts),
        "by_edge_cluster": dict(sorted(by_ec.items(), key=lambda kv: -kv[1])),
        "by_edge_cluster_actionable": dict(sorted(by_ec_actionable.items(), key=lambda kv: -kv[1])),
        "expected_alerts": sum(1 for a in alerts if a.expected),
        "pct_night_00_06": round(100 * night / tot),
        "pct_with_reaction": round(100 * sum(1 for a in alerts if a.seen or a.done) / tot),
        "storms": sorted({a.storm_id for a in alerts if a.storm_id}),
        "mtta_median_s": (sorted(acked)[len(acked) // 2] if acked else None),
        "human_actions": len(actions),
        "top_offender": max(by_ec, key=by_ec.get) if by_ec else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--out", default="data/floatip_scan.json")
    ap.add_argument("--skip-mtta", action="store_true", help="não buscar replies (mais rápido)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("defina SLACK_BOT_TOKEN", file=sys.stderr)
        return 1

    oldest = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()
    msgs = fetch_history(token, oldest)

    alerts: list[Alert] = []
    actions: list[HumanAction] = []
    for m in msgs:
        a = parse_alert(m)
        if a:
            alerts.append(a)
        elif m.get("user") and m.get("user") != BOT_USER and m.get("text") and "has joined" not in m["text"] and "has left" not in m["text"]:
            dt = datetime.fromtimestamp(float(m["ts"]), BRT)
            actions.append(HumanAction(ts=m["ts"], iso=dt.isoformat(), user=m["user"], text=m["text"]))

    attach_logs(alerts, msgs)
    mark_expected(alerts)
    tag_storms(alerts)
    if not args.skip_mtta:
        fetch_ack_times(token, alerts)

    out = {
        "meta": {
            "channel": CHANNEL_ID,
            "scanned_at": datetime.now(BRT).isoformat(),
            "window_days": args.days,
            "provenance": "OBS · Slack conversations.history",
            "severity_rule": "v1: (falha+alta_lat)/total — ▲▲>=30% ou perda de pacote · ▲>=15% · ◆<15%",
        },
        "summary": summarize(alerts, actions),
        "alerts": [asdict(a) for a in sorted(alerts, key=lambda x: -float(x.ts))],
        "human_actions": [asdict(h) for h in sorted(actions, key=lambda x: -float(x.ts))],
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"{len(alerts)} alertas · {len(actions)} atuações → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

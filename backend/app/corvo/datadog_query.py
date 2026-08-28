"""Corvo — QueryEngine: a ÚNICA fonte de agregação sobre o store.

Usado pelo relatório diário (collectors/corvo_datadog_report.py) e pelos
comandos da DM (app/corvo/bot.py). Nenhuma regra de métrica fora daqui e de
datadog_metrics.py.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from app.corvo.datadog_metrics import (
    EXACT_ACK_SOURCES,
    PageTimes,
    compute_page_times,
    histogram,
    stats,
)
from app.corvo.datadog_store import PageRow, Store, alert_key

BRT = timezone(timedelta(hours=-3), name="BRT")
REPORT_HOUR = 8  # 08:00 BRT — fim/início da janela diária
PERIOD_KINDS = ("hoje", "ontem", "7d", "30d", "mes", "mes_anterior")


def now_brt() -> datetime:
    return datetime.now(BRT)


def anchor_08(now: datetime) -> datetime:
    """Último 08:00 BRT <= now."""
    now = now.astimezone(BRT)
    a = now.replace(hour=REPORT_HOUR, minute=0, second=0, microsecond=0)
    if a > now:
        a -= timedelta(days=1)
    return a


def period(kind: str, now: datetime | None = None) -> tuple[float, float, str]:
    """(start_ts, end_ts, rótulo). Janelas: hoje = 08:00→agora (parcial);
    ontem = última janela fechada 08:00 D-1 → 08:00 D; 7d/30d móveis; mes =
    1º dia 00:00 BRT → agora; mes_anterior = mês fechado."""
    now = (now or now_brt()).astimezone(BRT)
    a = anchor_08(now)
    if kind == "hoje":
        s, e = a, now
        label = f"hoje (parcial) · {s:%d/%m %H:%M} → {e:%d/%m %H:%M}"
    elif kind == "ontem":
        s, e = a - timedelta(days=1), a
        label = f"{s:%d/%m %H:%M} → {e:%d/%m %H:%M}"
    elif kind == "7d":
        s, e = now - timedelta(days=7), now
        label = f"últimos 7 dias · {s:%d/%m} → {e:%d/%m}"
    elif kind == "30d":
        s, e = now - timedelta(days=30), now
        label = f"últimos 30 dias · {s:%d/%m} → {e:%d/%m}"
    elif kind == "mes":
        s = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        e = now
        label = f"mês de {s:%m/%Y} (até {e:%d/%m %H:%M})"
    elif re.fullmatch(r"\d{1,3}d", kind):
        n = int(kind[:-1])
        s, e = now - timedelta(days=n), now
        label = f"últimos {n} dias · {s:%d/%m} → {e:%d/%m}"
    elif kind == "mes_anterior":
        first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        s = (first - timedelta(days=1)).replace(day=1)
        e = first
        label = f"mês de {s:%m/%Y}"
    else:
        raise ValueError(f"período desconhecido: {kind}")
    return s.timestamp(), e.timestamp(), label


def daily_window(end_date: datetime, days: int = 1) -> tuple[float, float, str]:
    """Janela fechada terminando em 08:00 BRT de ``end_date`` (data), ``days`` dias."""
    e = end_date.astimezone(BRT).replace(hour=REPORT_HOUR, minute=0, second=0, microsecond=0)
    s = e - timedelta(days=days)
    label = f"{s:%d/%m %H:%M} → {e:%d/%m %H:%M}"
    return s.timestamp(), e.timestamp(), label


class QueryEngine:
    def __init__(self, store: Store):
        self.store = store

    # ------------------------------------------------------------ base
    def pages_with_times(self, start: float, end: float) -> list[tuple[PageRow, PageTimes]]:
        pages = self.store.pages_between(start, end)
        ids = [p.page_id for p in pages]
        trans = self.store.transitions_for(ids)
        events = self.store.human_events_for(ids)
        return [
            (p, compute_page_times(p, trans.get(p.page_id, []), events.get(p.page_id, [])))
            for p in pages
        ]

    def names(self) -> dict[str, str]:
        return self.store.user_names()

    def name(self, uid: str | None) -> str:
        if not uid:
            return "—"
        return self.store.user_name(uid) or uid

    # ------------------------------------------------------------ summary
    def summary(self, start: float, end: float, label: str = "") -> dict:
        rows = self.pages_with_times(start, end)
        pages = [p for p, _ in rows]
        times = [t for _, t in rows]
        total = len(pages)

        rec7 = self.store.recurrence(end - 7 * 86400, end)
        rec30 = self.store.recurrence(end - 30 * 86400, end)
        recday = self.store.recurrence(start, end)

        by_team = Counter(p.team or "?" for p in pages)
        by_urgency = Counter(p.urgency or "?" for p in pages)
        by_status = Counter(p.status or "?" for p in pages)
        by_kind = Counter(p.kind for p in pages)
        by_dc = Counter(p.dc or "?" for p in pages)
        by_origem = Counter(p.origem or "?" for p in pages)

        responders: dict[str, dict] = defaultdict(lambda: {"pages": 0, "silent_ack": 0, "resp": []})
        for p, t in rows:
            if p.responder:
                r = responders[p.responder]
                r["pages"] += 1
                if t.silent_ack:
                    r["silent_ack"] += 1
                if t.response_s is not None:
                    r["resp"].append(t.response_s)
        slack_responders = Counter()
        for _, t in rows:
            for u in t.slack_users:
                slack_responders[u] += 1
        responder_table = sorted(
            (
                {
                    "user": u,
                    "name": self.name(u),
                    "pages": v["pages"],
                    "silent_ack": v["silent_ack"],
                    "response": stats(v["resp"]),
                }
                for u, v in responders.items()
            ),
            key=lambda x: -x["pages"],
        )

        resp_vals = [t.response_s for t in times]
        ack_exact = [t.ack_s for t in times if t.ack_source in EXACT_ACK_SOURCES]
        ack_all = [t.ack_s for t in times if t.ack_s is not None]
        first_touch = [t.first_touch_s for t in times]
        resolve_vals = [t.resolve_s for t in times]
        unanswered = [p for p, t in rows if t.unanswered]
        silent = [p for p, t in rows if t.silent_ack]

        recurrent_day = [
            {"key": k, "count": c, "d7": rec7["alert"].get(k, 0), "d30": rec30["alert"].get(k, 0)}
            for k, c in sorted(recday["alert"].items(), key=lambda kv: -kv[1])
            if c >= 2
        ]
        recurrent_inc = [
            {"inc": k, "count": c, "d7": rec7["inc"].get(k, 0), "d30": rec30["inc"].get(k, 0)}
            for k, c in sorted(recday["inc"].items(), key=lambda kv: -kv[1])
            if c >= 2
        ]
        top7 = [
            {"key": k, "count": c}
            for k, c in sorted(rec7["alert"].items(), key=lambda kv: -kv[1])[:10]
        ]
        top30 = [
            {"key": k, "count": c}
            for k, c in sorted(rec30["alert"].items(), key=lambda kv: -kv[1])[:10]
        ]

        page_rows = []
        for p, t in rows:
            ak = alert_key(p.servidor, p.evento)
            page_rows.append(
                {
                    **_page_dict(p),
                    **t.as_dict(),
                    "responder_name": self.name(p.responder) if p.responder else None,
                    "response_user_name": self.name(t.response_user) if t.response_user else None,
                    "d7": rec7["alert"].get(ak, 0) if ak else 0,
                    "d30": rec30["alert"].get(ak, 0) if ak else 0,
                }
            )

        oncall = self.oncall(at_ts=end)
        return {
            "window": {
                "start": start,
                "end": end,
                "label": label,
                "start_iso": _iso(start),
                "end_iso": _iso(end),
            },
            "total": total,
            "by_kind": dict(by_kind),
            "by_team": dict(by_team.most_common()),
            "by_urgency": dict(by_urgency.most_common()),
            "by_status": dict(by_status.most_common()),
            "by_dc": dict(by_dc.most_common()),
            "by_origem": dict(by_origem.most_common()),
            "response": stats(resp_vals),
            "first_touch": stats(first_touch),
            "ack_exact": stats(ack_exact),
            "ack_all": stats(ack_all),
            "ack_sources": dict(Counter(t.ack_source or "none" for t in times)),
            "resolve": stats(resolve_vals),
            "unanswered": [_page_dict(p) for p in unanswered],
            "unanswered_pct": round(100 * len(unanswered) / total) if total else 0,
            "silent_ack": [_page_dict(p) for p in silent],
            "responders": responder_table,
            "slack_responders": [
                {"user": u, "name": self.name(u), "events": c}
                for u, c in slack_responders.most_common()
            ],
            "recurrent_day": recurrent_day,
            "recurrent_inc": recurrent_inc,
            "top_7d": top7,
            "top_30d": top30,
            "histogram": histogram(resp_vals),
            "manual": [r for r in page_rows if r["kind"] == "manual"],
            "unknown_dc": sorted({p.servidor for p in pages if p.dc is None and p.servidor}),
            "oncall": oncall,
            "pages": page_rows,
        }

    # ------------------------------------------------------------ consultas
    def count_month(self, now: datetime | None = None) -> dict:
        s, e, label = period("mes", now)
        ps, pe, plabel = period("mes_anterior", now)
        cur = self.store.pages_between(s, e)
        prev = self.store.pages_between(ps, pe)
        return {
            "label": label,
            "total": len(cur),
            "prev_label": plabel,
            "prev_total": len(prev),
            "by_team": dict(Counter(p.team or "?" for p in cur).most_common()),
            "by_dc": dict(Counter(p.dc or "?" for p in cur).most_common()),
            "by_kind": dict(Counter(p.kind for p in cur)),
            "by_urgency": dict(Counter(p.urgency or "?" for p in cur).most_common()),
        }

    def response_stats(self, start: float, end: float) -> dict:
        rows = self.pages_with_times(start, end)
        times = [t for _, t in rows]
        return {
            "total": len(rows),
            "response": stats([t.response_s for t in times]),
            "ack_exact": stats([t.ack_s for t in times if t.ack_source in EXACT_ACK_SOURCES]),
            "ack_all": stats([t.ack_s for t in times if t.ack_s is not None]),
            "first_touch": stats([t.first_touch_s for t in times]),
            "resolve": stats([t.resolve_s for t in times]),
            "unanswered": sum(1 for t in times if t.unanswered),
            "silent_ack": sum(1 for t in times if t.silent_ack),
            "ack_sources": dict(Counter(t.ack_source or "none" for t in times)),
        }

    def top_dcs(self, start: float, end: float, limit: int = 10) -> list[dict]:
        pages = self.store.pages_between(start, end)
        c = Counter(p.dc or "?" for p in pages)
        total = len(pages) or 1
        return [
            {"dc": dc, "count": n, "pct": round(100 * n / total)} for dc, n in c.most_common(limit)
        ]

    def recurrent(self, start: float, end: float, limit: int = 10) -> dict:
        rec = self.store.recurrence(start, end)
        return {
            "alert": [
                {"key": k, "count": c}
                for k, c in sorted(rec["alert"].items(), key=lambda kv: -kv[1])[:limit]
                if c >= 2
            ],
            "inc": [
                {"inc": k, "count": c}
                for k, c in sorted(rec["inc"].items(), key=lambda kv: -kv[1])[:limit]
                if c >= 2
            ],
        }

    def unanswered(self, start: float, end: float) -> list[dict]:
        return [_page_dict(p) for p, t in self.pages_with_times(start, end) if t.unanswered]

    def oncall(self, at_ts: float | None = None) -> dict:
        h = self.store.latest_handover(before_ts=at_ts)
        out = {}
        for sched in ("Interna", "Externa"):
            r = h.get(sched)
            if not r:
                out[sched] = None
                continue
            entry = {
                "user": r["user"],
                "name": r["name"] or (self.name(r["user"]) if r["user"] else None),
                "since": r["date"],
                "since_hm": datetime.fromtimestamp(float(r["msg_ts"]), BRT).strftime("%d/%m %H:%M"),
                "last": None,
            }
            if not r["user"]:
                # schedule vazio (horário comercial): quem foi o último de plantão
                last = self.store.last_handover_with_user(sched, at_ts)
                if last:
                    entry["last"] = {
                        "user": last["user"],
                        "name": last["name"] or self.name(last["user"]),
                        "since": last["date"],
                    }
            out[sched] = entry
        return out

    def page_card(self, ident: str) -> dict | None:
        p = self.store.find_page(ident)
        if not p:
            return None
        trans = self.store.transitions_for([p.page_id]).get(p.page_id, [])
        events = self.store.human_events_for([p.page_id]).get(p.page_id, [])
        t = compute_page_times(p, trans, events)
        ak = alert_key(p.servidor, p.evento)
        rec7 = self.store.recurrence(p.t0 - 7 * 86400, p.t0 + 1)
        rec30 = self.store.recurrence(p.t0 - 30 * 86400, p.t0 + 1)
        same_inc = [q for q in self.store.pages_by_inc(p.inc)] if p.inc else []
        return {
            **_page_dict(p),
            **t.as_dict(),
            "responder_name": self.name(p.responder) if p.responder else None,
            "response_user_name": self.name(t.response_user) if t.response_user else None,
            "timeline": [
                {
                    "status": x.status,
                    "ts": x.event_ts,
                    "iso": _iso(x.event_ts),
                    "source": x.source,
                    "responder": x.responder,
                    "responder_name": self.name(x.responder) if x.responder else None,
                }
                for x in sorted(trans, key=lambda x: x.event_ts)
            ],
            "events": [
                {
                    "kind": e.kind,
                    "ts": e.event_ts,
                    "iso": _iso(e.event_ts),
                    "user": e.user,
                    "name": self.name(e.user),
                    "text": (e.text or "")[:200],
                    "attribution": e.attribution,
                }
                for e in sorted(events, key=lambda e: e.event_ts)
            ],
            "d7": rec7["alert"].get(ak, 0) if ak else 0,
            "d30": rec30["alert"].get(ak, 0) if ak else 0,
            "same_inc": [
                {"page_id": q.page_id, "iso": _iso(q.t0), "status": q.status} for q in same_inc
            ],
        }


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, BRT).isoformat(timespec="seconds")


def _page_dict(p: PageRow) -> dict:
    return {
        "page_id": p.page_id,
        "page_url": p.page_url,
        "msg_ts": p.msg_ts,
        "t0": p.t0,
        "iso": _iso(p.t0),
        "hora": datetime.fromtimestamp(p.t0, BRT).strftime("%d/%m %H:%M"),
        "kind": p.kind,
        "title": p.title,
        "status": p.status,
        "urgency": p.urgency,
        "team": p.team,
        "responder": p.responder,
        "servidor": p.servidor,
        "evento": p.evento,
        "descricao": p.descricao,
        "inc": p.inc,
        "origem": p.origem,
        "dc": p.dc,
        "requested_by": p.requested_by,
        "justificativa": p.justificativa,
        "reply_count": p.reply_count,
        "reactions": [r.get("name") for r in p.reactions],
        "channel": p.channel,
    }

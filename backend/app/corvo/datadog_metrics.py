"""Corvo — métricas puras das pages do Datadog (sem I/O).

Definições (ver docs/runbook-corvo-datadog.md):
- t0 = ts da mensagem do Datadog.
- response_s  = 1ª mensagem humana atribuída à page − t0 (thread > menção > mais próxima).
- reaction_s  = 1ª reação humana − t0 (só existe com evento ao vivo).
- ack_s       = transição Acknowledged − t0; fonte: live > edited_ts > proxy (= response_s).
- resolve_s   = transição Resolved − t0 (live ou edited_ts).
- first_touch = menor entre response/reaction/ack(exato).
- unanswered  = sem first_touch e sem Responder; silent_ack = Responder sem sinal humano no Slack.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from app.corvo.datadog_store import HumanEventRow, PageRow, TransitionRow

EXACT_ACK_SOURCES = ("live", "edited_ts")


@dataclass
class PageTimes:
    page_id: int
    response_s: int | None = None
    response_user: str | None = None
    response_attr: str | None = None
    reaction_s: int | None = None
    reacted: bool = False
    ack_s: int | None = None
    ack_source: str | None = None
    resolve_s: int | None = None
    resolve_source: str | None = None
    first_touch_s: int | None = None
    unanswered: bool = False
    silent_ack: bool = False
    slack_users: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def compute_page_times(
    page: PageRow, transitions: list[TransitionRow], events: list[HumanEventRow]
) -> PageTimes:
    t0 = page.t0
    pt = PageTimes(page_id=page.page_id)

    msgs = sorted(
        (e for e in events if e.kind in ("reply", "channel_msg") and e.event_ts >= t0),
        key=lambda e: e.event_ts,
    )
    if msgs:
        pt.response_s = int(msgs[0].event_ts - t0)
        pt.response_user = msgs[0].user
        pt.response_attr = msgs[0].attribution
    reactions = sorted(
        (e for e in events if e.kind == "reaction" and e.event_ts >= t0), key=lambda e: e.event_ts
    )
    if reactions:
        pt.reaction_s = int(reactions[0].event_ts - t0)
    pt.reacted = bool(reactions) or bool(page.reactions)
    pt.slack_users = sorted({e.user for e in events if e.user})

    live = {t.status: t for t in transitions if t.source == "live"}
    hist = {t.status: t for t in transitions if t.source == "history"}

    ack = live.get("Acknowledged")
    if ack and ack.event_ts >= t0:
        pt.ack_s, pt.ack_source = int(ack.event_ts - t0), "live"
    elif page.status == "Acknowledged" and page.edited_ts and page.edited_ts >= t0:
        pt.ack_s, pt.ack_source = int(page.edited_ts - t0), "edited_ts"
    elif "Acknowledged" in hist and hist["Acknowledged"].event_ts >= t0:
        pt.ack_s, pt.ack_source = int(hist["Acknowledged"].event_ts - t0), "edited_ts"
    elif page.status == "Resolved" and page.responder and pt.response_s is not None:
        pt.ack_s, pt.ack_source = pt.response_s, "proxy"

    res = live.get("Resolved")
    if res and res.event_ts >= t0:
        pt.resolve_s, pt.resolve_source = int(res.event_ts - t0), "live"
    elif page.status == "Resolved" and page.edited_ts and page.edited_ts >= t0:
        pt.resolve_s, pt.resolve_source = int(page.edited_ts - t0), "edited_ts"

    candidates = [pt.response_s, pt.reaction_s]
    if pt.ack_source in EXACT_ACK_SOURCES:
        candidates.append(pt.ack_s)
    vals = [c for c in candidates if c is not None]
    pt.first_touch_s = min(vals) if vals else None

    pt.unanswered = pt.first_touch_s is None and not page.responder
    pt.silent_ack = bool(page.responder) and not msgs and not reactions
    return pt


# ------------------------------------------------------------------ atribuição
_PAGE_REF_RE = re.compile(r"#\s?(\d{4,6})\b")


@dataclass
class PageRef:
    page_id: int
    t0: float
    servidor: str | None
    inc: str | None


def attribute_channel_message(
    ts: float, text: str, pages: list[PageRef], answered: set[int], window_s: int = 1800
) -> tuple[int | None, str | None]:
    """Atribui uma mensagem humana top-level do canal a uma page.
    (1) menção explícita (#page, servidor, INC); (2) page mais recente ainda
    sem resposta, disparada há <= window_s. Retorna (page_id, attribution)."""
    low = (text or "").lower()
    recent = [p for p in pages if 0 <= ts - p.t0 <= window_s]
    for m in _PAGE_REF_RE.finditer(low):
        pid = int(m.group(1))
        for p in pages:
            if p.page_id == pid:
                return pid, "mention"
    for p in sorted(recent, key=lambda p: -p.t0):
        if p.servidor and p.servidor.lower() in low:
            return p.page_id, "mention"
        if p.inc and p.inc.lower() in low:
            return p.page_id, "mention"
    for p in sorted(recent, key=lambda p: -p.t0):
        if p.page_id not in answered:
            return p.page_id, "nearest"
    return None, None


# ------------------------------------------------------------------ agregados
def median(values: list[int | float]) -> float | None:
    v = sorted(values)
    if not v:
        return None
    n = len(v)
    return float(v[n // 2]) if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def percentile(values: list[int | float], p: float) -> float | None:
    """Nearest-rank: p em [0, 100]."""
    v = sorted(values)
    if not v:
        return None
    import math

    k = max(1, math.ceil(p / 100 * len(v)))
    return float(v[min(k, len(v)) - 1])


def stats(values: list[int | float]) -> dict:
    vals = [x for x in values if x is not None]
    return {
        "n": len(vals),
        "median": median(vals),
        "p90": percentile(vals, 90),
        "max": max(vals) if vals else None,
        "mean": (sum(vals) / len(vals)) if vals else None,
    }


HISTOGRAM_BINS = (
    ("<5m", 0, 300),
    ("5–15m", 300, 900),
    ("15–30m", 900, 1800),
    ("30–60m", 1800, 3600),
    (">60m", 3600, None),
)


def histogram(values: list[int | None]) -> list[dict]:
    out = [{"label": lbl, "count": 0} for lbl, _, _ in HISTOGRAM_BINS]
    out.append({"label": "sem resposta no Slack", "count": 0})
    for v in values:
        if v is None:
            out[-1]["count"] += 1
            continue
        for i, (_, lo, hi) in enumerate(HISTOGRAM_BINS):
            if v >= lo and (hi is None or v < hi):
                out[i]["count"] += 1
                break
    return out


def fmt_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "—"
    s = int(round(seconds))
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h}h{m:02d}"
    d, h = divmod(h, 24)
    return f"{d}d{h:02d}h"

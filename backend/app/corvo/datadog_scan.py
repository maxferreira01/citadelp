"""Corvo — varredura do histórico do #datadog-redes → store.

Usada pelo job do relatório (janela do dia) e pelo bot (gap-fill no start).
Só leitura no Slack. Transições derivadas do histórico recebem ``source='history'``
e nunca sobrescrevem as ``live`` gravadas pelo bot.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from app.corvo import slack_client as sc
from app.corvo.datadog import (
    DATADOG_BOT_USER,
    attachment_text,
    is_handover,
    parse_datadog_page,
    parse_handover,
)
from app.corvo.datadog_metrics import PageRef, attribute_channel_message
from app.corvo.datadog_query import BRT
from app.corvo.datadog_store import Store

SKIP_SUBTYPES = {
    "channel_join",
    "channel_leave",
    "bot_add",
    "bot_remove",
    "channel_topic",
    "channel_purpose",
    "group_join",
    "group_leave",
    "tombstone",
}


@dataclass
class ScanResult:
    pages: int = 0
    pages_new: int = 0
    handovers: int = 0
    human_msgs: int = 0
    replies_fetched: int = 0
    unparsed_bot_msgs: list[dict] = field(default_factory=list)
    raw: list[dict] = field(default_factory=list)


def is_human(msg: dict, ignore_users: set[str]) -> bool:
    if not msg.get("user") or msg.get("bot_id"):
        return False
    if msg.get("user") in ignore_users:
        return False
    if msg.get("subtype") in SKIP_SUBTYPES:
        return False
    return True


def derive_history_transitions(store: Store, page: dict, msg: dict) -> None:
    """Estado atual + edited.ts → transições 'history'. O ack exato só vem do bot."""
    pid = page["page_id"]
    t0 = float(msg["ts"])
    store.add_transition(pid, "Triggered", None, t0, None, "history")
    edited = msg.get("edited") or {}
    ets = float(edited["ts"]) if edited.get("ts") else None
    if page.get("status") == "Acknowledged" and ets:
        store.add_transition(pid, "Acknowledged", page.get("responder"), ets, ets, "history")
    elif page.get("status") == "Resolved" and ets:
        store.add_transition(pid, "Resolved", page.get("responder"), ets, ets, "history")


def scan_channel(
    client,
    store: Store,
    channel: str,
    oldest: float,
    latest: float | None = None,
    fetch_replies: bool = True,
    ignore_users: set[str] | None = None,
    response_window_s: int = 1800,
    keep_raw: bool = False,
    sleep: float = sc.TIER3_SLEEP,
) -> ScanResult:
    ignore = {DATADOG_BOT_USER} | (ignore_users or set())
    now = time.time()
    res = ScanResult()
    msgs = sc.fetch_history(client, channel, oldest, latest, sleep=sleep)
    if keep_raw:
        res.raw = msgs
    msgs.sort(key=lambda m: float(m["ts"]))

    refs: list[PageRef] = []
    answered: set[int] = set()
    humans: list[dict] = []
    names: dict[str, str] = store.user_names()

    for m in msgs:
        ts = m["ts"]
        if m.get("user") == DATADOG_BOT_USER or (m.get("bot_id") and not m.get("user")):
            blob = attachment_text(m)
            page = parse_datadog_page(blob)
            if page:
                existed = store.page_by_msg_ts(ts) is not None
                store.upsert_page(page, m, channel, now)
                derive_history_transitions(store, page, m)
                res.pages += 1
                res.pages_new += 0 if existed else 1
                refs.append(
                    PageRef(page["page_id"], float(ts), page.get("servidor"), page.get("inc"))
                )
                if fetch_replies and int(m.get("reply_count") or 0) > 0:
                    _ingest_replies(
                        client, store, channel, page["page_id"], ts, ignore, sleep, names
                    )
                    res.replies_fetched += 1
                    answered.add(page["page_id"])
                if page.get("responder"):
                    _ensure_name(client, store, page["responder"], names)
                continue
            if is_handover(blob):
                h = parse_handover(blob)
                if h:
                    date = datetime.fromtimestamp(float(ts), BRT).strftime("%Y-%m-%d")
                    for sched, uid in h["schedules"].items():
                        store.upsert_handover(
                            date, sched, uid, h["names"].get(uid) if uid else None, ts
                        )
                        if uid:
                            if h["names"].get(uid):
                                store.set_user_name(uid, h["names"][uid], now)
                                names[uid] = h["names"][uid]
                            else:
                                _ensure_name(client, store, uid, names)
                    res.handovers += 1
                continue
            res.unparsed_bot_msgs.append({"ts": ts, "text": blob[:200]})
            continue
        if is_human(m, ignore) and m.get("thread_ts", ts) == ts:
            humans.append(m)

    # mensagens humanas top-level do canal: atribuição a uma page
    for m in humans:
        ts = float(m["ts"])
        pid, attr = attribute_channel_message(
            ts, m.get("text", ""), refs, answered, response_window_s
        )
        if store.add_human_event(pid, m["ts"], ts, "channel_msg", m["user"], m.get("text"), attr):
            res.human_msgs += 1
        if pid is not None:
            answered.add(pid)
        _ensure_name(client, store, m["user"], names)

    store.set_meta("last_scan_at", f"{now:.0f}")
    return res


def _ingest_replies(
    client,
    store: Store,
    channel: str,
    page_id: int,
    ts: str,
    ignore: set[str],
    sleep: float,
    names: dict[str, str],
) -> None:
    try:
        replies = sc.fetch_replies(client, channel, ts, sleep=sleep)
    except Exception:  # noqa: BLE001 — thread apagada/sem permissão: segue sem replies
        return
    time.sleep(sleep)
    for r in replies:
        if not is_human(r, ignore):
            continue
        store.add_human_event(
            page_id, r["ts"], float(r["ts"]), "reply", r["user"], r.get("text"), "thread"
        )
        _ensure_name(client, store, r["user"], names)


def _ensure_name(client, store: Store, uid: str, names: dict[str, str]) -> None:
    if uid in names or client is None:
        return
    name = sc.user_name(client, uid, names)
    store.set_user_name(uid, name)

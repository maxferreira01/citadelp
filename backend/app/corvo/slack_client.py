"""Corvo — wrapper fino do slack_sdk.WebClient (import tardio: o pacote base
da API não depende de slack_sdk; só o grupo opcional ``[bot]``)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

TIER3_SLEEP = 1.1  # conversations.history/replies: ~50 req/min


def make_client(token: str):
    from slack_sdk import WebClient
    from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

    client = WebClient(token=token)
    client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=3))
    return client


def fetch_history(
    client, channel: str, oldest: float, latest: float | None = None, sleep: float = TIER3_SLEEP
) -> list[dict]:
    """Todas as mensagens top-level em [oldest, latest], paginadas."""
    msgs: list[dict] = []
    cursor = None
    while True:
        kw: dict[str, Any] = {
            "channel": channel,
            "limit": 200,
            "oldest": f"{oldest:.6f}",
            "inclusive": True,
        }
        if latest is not None:
            kw["latest"] = f"{latest:.6f}"
        if cursor:
            kw["cursor"] = cursor
        resp = client.conversations_history(**kw)
        msgs.extend(resp.get("messages", []))
        cursor = (resp.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(sleep)
    return msgs


def fetch_replies(client, channel: str, ts: str, sleep: float = TIER3_SLEEP) -> list[dict]:
    """Replies da thread (sem a mensagem-pai)."""
    out: list[dict] = []
    cursor = None
    while True:
        kw: dict[str, Any] = {"channel": channel, "ts": ts, "limit": 200}
        if cursor:
            kw["cursor"] = cursor
        resp = client.conversations_replies(**kw)
        msgs = resp.get("messages", [])
        out.extend(m for m in msgs if m.get("ts") != ts)
        cursor = (resp.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(sleep)
    return out


def user_name(client, user_id: str, cache: dict[str, str]) -> str:
    if user_id in cache:
        return cache[user_id]
    try:
        resp = client.users_info(user=user_id)
        u = resp["user"]
        name = (
            (u.get("profile") or {}).get("display_name")
            or u.get("real_name")
            or u.get("name")
            or user_id
        )
    except Exception:  # noqa: BLE001 — nome é cosmético; nunca derruba o job
        name = user_id
    cache[user_id] = name
    return name


def open_dm(client, user_id: str) -> str:
    resp = client.conversations_open(users=[user_id])
    return resp["channel"]["id"]


def post_blocks(
    client, channel: str, blocks: list[dict], text: str, thread_ts: str | None = None
) -> str:
    kw: dict[str, Any] = {"channel": channel, "blocks": blocks, "text": text, "unfurl_links": False}
    if thread_ts:
        kw["thread_ts"] = thread_ts
    resp = client.chat_postMessage(**kw)
    return resp["ts"]


def upload_file(
    client,
    channel: str,
    path: Path,
    title: str,
    thread_ts: str | None = None,
    initial_comment: str | None = None,
) -> dict:
    kw: dict[str, Any] = {
        "channel": channel,
        "file": str(path),
        "filename": path.name,
        "title": title,
    }
    if thread_ts:
        kw["thread_ts"] = thread_ts
    if initial_comment:
        kw["initial_comment"] = initial_comment
    return client.files_upload_v2(**kw).data


def permalink(client, channel: str, ts: str) -> str | None:
    try:
        return client.chat_getPermalink(channel=channel, message_ts=ts)["permalink"]
    except Exception:  # noqa: BLE001
        return None

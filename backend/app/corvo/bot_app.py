"""Corvo — app Slack (slack_bolt, Socket Mode). Fino: eventos → store; DM → bot.handle.

``apply_event`` é pura (store + evento) e testada; o resto é wiring.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

from app.corvo import slack_client as sc
from app.corvo.bot import BUTTON_ACTION_RE, Reply, handle, is_allowed, route
from app.corvo.datadog import attachment_text, is_handover, parse_datadog_page, parse_handover
from app.corvo.datadog_metrics import PageRef, attribute_channel_message
from app.corvo.datadog_query import BRT, QueryEngine, now_brt, period
from app.corvo.datadog_report import render_html, render_pdf, write_artifacts
from app.corvo.datadog_scan import SKIP_SUBTYPES, scan_channel
from app.corvo.datadog_store import Store
from app.corvo.settings import Settings

log = logging.getLogger("corvo.bot")


# ------------------------------------------------------------------ eventos (puro)
def apply_event(
    store: Store,
    event: dict,
    channel_id: str,
    datadog_user: str,
    self_user: str | None = None,
    response_window_s: int = 1800,
    names: dict[str, str] | None = None,
) -> str:
    """Aplica um evento do canal ao store. Retorna um rótulo do que fez (p/ log e teste)."""
    etype = event.get("type")
    if etype == "reaction_added":
        item = event.get("item") or {}
        if item.get("channel") != channel_id or item.get("type") != "message":
            return "ignored"
        user = event.get("user")
        if not user or user in {datadog_user, self_user}:
            return "ignored"
        page = store.page_by_msg_ts(item.get("ts", ""))
        if not page:
            return "reaction_no_page"
        ts = float(event.get("event_ts") or time.time())
        store.add_human_event(
            page.page_id, item.get("ts"), ts, "reaction", user, event.get("reaction"), "reaction"
        )
        return "reaction"

    if etype != "message" or event.get("channel") != channel_id:
        return "ignored"
    subtype = event.get("subtype")

    if subtype == "message_changed":
        new = event.get("message") or {}
        prev = event.get("previous_message") or {}
        if new.get("user") != datadog_user and not new.get("bot_id"):
            return "ignored"
        page = parse_datadog_page(attachment_text(new))
        if not page:
            return "changed_no_page"
        ts_msg = new.get("ts") or event.get("previous_message", {}).get("ts")
        msg = {**new, "ts": ts_msg}
        store.upsert_page(page, msg, channel_id, time.time())
        old_status = None
        if prev:
            oldp = parse_datadog_page(attachment_text(prev))
            old_status = oldp.get("status") if oldp else None
        edited = (new.get("edited") or {}).get("ts")
        ets = float(edited) if edited else None
        ev_ts = float(event.get("event_ts") or event.get("ts") or time.time())
        if page.get("status") and page["status"] != old_status:
            store.add_transition(
                page["page_id"],
                page["status"],
                page.get("responder"),
                ev_ts,
                ets,
                "live",
                raw={"old": old_status, "new": page["status"]},
            )
            return f"transition:{old_status}->{page['status']}"
        return "changed_same_status"

    if subtype in SKIP_SUBTYPES or subtype == "message_deleted":
        return "ignored"

    user = event.get("user")
    ts = event.get("ts")
    if user == datadog_user or (event.get("bot_id") and not user):
        blob = attachment_text(event)
        page = parse_datadog_page(blob)
        if page:
            store.upsert_page(page, event, channel_id, time.time())
            store.add_transition(page["page_id"], "Triggered", None, float(ts), None, "live")
            if page.get("status") and page["status"] != "Triggered":
                store.add_transition(
                    page["page_id"], page["status"], page.get("responder"), float(ts), None, "live"
                )
            return "page"
        if is_handover(blob):
            h = parse_handover(blob)
            if h:
                date = datetime.fromtimestamp(float(ts), BRT).strftime("%Y-%m-%d")
                for sched, uid in h["schedules"].items():
                    store.upsert_handover(
                        date, sched, uid, h["names"].get(uid) if uid else None, ts
                    )
                    if uid and h["names"].get(uid):
                        store.set_user_name(uid, h["names"][uid])
                return "handover"
        return "bot_other"

    if not user or user == self_user:
        return "ignored"
    thread_ts = event.get("thread_ts")
    if thread_ts and thread_ts != ts:
        page = store.page_by_msg_ts(thread_ts)
        if page:
            store.add_human_event(
                page.page_id, ts, float(ts), "reply", user, event.get("text"), "thread"
            )
            store.bump_reply_count(page.page_id)
            return "reply"
        return "reply_no_page"
    # mensagem humana top-level no canal
    now_ts = float(ts)
    recent = store.pages_between(now_ts - response_window_s, now_ts + 1)
    ev = store.human_events_for([p.page_id for p in recent])
    answered = {
        pid for pid, lst in ev.items() if any(e.kind in ("reply", "channel_msg") for e in lst)
    }
    refs = [PageRef(p.page_id, p.t0, p.servidor, p.inc) for p in recent]
    pid, attr = attribute_channel_message(
        now_ts, event.get("text", ""), refs, answered, response_window_s
    )
    store.add_human_event(pid, ts, now_ts, "channel_msg", user, event.get("text"), attr)
    return f"channel_msg:{attr}"


# ------------------------------------------------------------------ contexto do bot
class Ctx:
    def __init__(self, settings: Settings, store: Store, client):
        self.settings = settings
        self.store = store
        self.client = client
        self.engine = QueryEngine(store)

    def render_pdf_for(self, kind: str, now: datetime) -> Path | None:
        s, e, label = period(kind, now)
        sm = self.engine.summary(s, e, label)
        html = render_html(sm)
        pdf = render_pdf(html)
        art = write_artifacts(
            self.settings.report_dir,
            sm,
            html,
            pdf,
            kind=kind,
            stamp=f"{datetime.fromtimestamp(e, BRT):%Y-%m-%d}",
        )
        self.store.add_report(
            s,
            e,
            kind,
            str(art.html_path),
            str(art.pdf_path) if art.pdf_path else None,
            str(art.json_path),
            None,
            None,
            time.time(),
        )
        return art.pdf_path or art.html_path

    def last_pdf(self) -> Path | None:
        r = self.store.last_report(with_pdf=True) or self.store.last_report(with_pdf=False)
        if not r:
            return None
        p = Path(r["pdf_path"] or r["html_path"])
        return p if p.is_file() else None


def send_reply(client, channel: str, reply: Reply, thread_ts: str | None = None) -> None:
    ts = sc.post_blocks(client, channel, reply.blocks, reply.text, thread_ts=thread_ts)
    if reply.file and reply.file.is_file():
        sc.upload_file(
            client, channel, reply.file, reply.file_title or reply.file.name, thread_ts=ts
        )


# ------------------------------------------------------------------ wiring do bolt
def build_app(settings: Settings, store: Store | None = None):
    from slack_bolt import App

    if not settings.slack_bot_token or not settings.slack_app_token:
        raise SystemExit("defina SLACK_BOT_TOKEN e SLACK_APP_TOKEN no .env")
    store = store or Store(settings.db_path)
    app = App(token=settings.slack_bot_token)
    client = app.client
    try:
        settings.self_user = client.auth_test()["user_id"]
    except Exception as exc:  # noqa: BLE001
        log.warning("auth.test falhou: %s", exc)
    ctx = Ctx(settings, store, client)
    names: dict[str, str] = store.user_names()

    @app.event("message")
    def on_message(event, say, logger):  # noqa: ANN001
        ch = event.get("channel")
        if ch == settings.channel_id:
            try:
                what = apply_event(
                    store,
                    event,
                    settings.channel_id,
                    settings.datadog_bot_user,
                    settings.self_user,
                    settings.response_window_s,
                    names,
                )
                logger.info("canal: %s", what)
            except Exception:  # noqa: BLE001
                logger.exception("erro aplicando evento do canal")
            return
        if event.get("channel_type") == "im" and not event.get("subtype") and event.get("user"):
            _on_dm(event, say, logger)

    def _on_dm(event, say, logger):  # noqa: ANN001
        user = event["user"]
        if user == settings.self_user:
            return
        if not is_allowed(user, settings.allowed_users):
            say(text="Este app responde só aos usuários autorizados (CORVO_BOT_ALLOWED_USERS).")
            return
        cmd = route(event.get("text", ""))
        logger.info("dm de %s: %s → %s", user, event.get("text", "")[:60], cmd.name)
        if cmd.name == "resumo":
            say(text=f"⏳ gerando o resumo ({cmd.period}) e o PDF…")
        try:
            reply = handle(cmd, ctx, now_brt())
        except Exception:  # noqa: BLE001
            logger.exception("erro no comando %s", cmd.name)
            say(text=f"Deu erro ao executar `{cmd.name}` — veja o journal do corvo-datadog-bot.")
            return
        send_reply(client, event["channel"], reply)

    @app.event("reaction_added")
    def on_reaction(event, logger):  # noqa: ANN001
        try:
            what = apply_event(
                store,
                event,
                settings.channel_id,
                settings.datadog_bot_user,
                settings.self_user,
                settings.response_window_s,
                names,
            )
            logger.info("reação: %s", what)
        except Exception:  # noqa: BLE001
            logger.exception("erro aplicando reação")

    @app.action({"action_id": BUTTON_ACTION_RE})
    def on_button(ack, body, logger):  # noqa: ANN001
        ack()
        user = (body.get("user") or {}).get("id", "")
        value = ((body.get("actions") or [{}])[0]).get("value", "ajuda")
        channel = (body.get("channel") or {}).get("id") or (body.get("container") or {}).get(
            "channel_id"
        )
        logger.info("botão de %s: %s (canal %s)", user, value, channel)
        if not is_allowed(user, settings.allowed_users) or not channel:
            return
        try:
            cmd = route(value)
            if cmd.name == "resumo":
                client.chat_postMessage(
                    channel=channel, text=f"⏳ gerando o resumo ({cmd.period}) e o PDF…"
                )
            reply = handle(cmd, ctx, now_brt())
            send_reply(client, channel, reply)
        except Exception:  # noqa: BLE001
            logger.exception("erro no botão %s", value)

    return app, store, ctx


def gap_fill(settings: Settings, store: Store, client, days_default: int = 2) -> None:
    """No start: re-lê o canal desde o último evento ao vivo (máx. N dias)."""
    last = store.last_live_event_ts() or store.last_page_ts()
    oldest = max(last or 0, time.time() - days_default * 86400)
    try:
        res = scan_channel(
            client,
            store,
            settings.channel_id,
            oldest,
            ignore_users={settings.self_user} if settings.self_user else None,
            response_window_s=settings.response_window_s,
        )
        log.info(
            "gap-fill: %d pages (%d novas), %d handovers", res.pages, res.pages_new, res.handovers
        )
    except Exception:  # noqa: BLE001
        log.exception("gap-fill falhou (segue só com eventos ao vivo)")


def run() -> int:
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logging.getLogger("weasyprint").setLevel(logging.WARNING)
    logging.getLogger("fontTools").setLevel(logging.WARNING)
    settings = Settings.from_env()
    app, store, _ctx = build_app(settings)
    gap_fill(settings, store, app.client)
    log.info("Corvo · Datadog bot ouvindo %s (Socket Mode)", settings.channel_id)
    SocketModeHandler(app, settings.slack_app_token).start()
    return 0

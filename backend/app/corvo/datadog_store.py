"""Corvo — store SQLite das pages do Datadog On-Call.

Um arquivo (``data/corvo_datadog.sqlite``), dois escritores esporádicos: o bot
(eventos ao vivo) e o job do relatório (scan do histórico). WAL + busy_timeout.

Regra de ouro das transições: ``source='live'`` (evento ``message_changed``)
sempre vence ``source='history'`` (derivada do estado atual + ``edited.ts``).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    page_id INTEGER PRIMARY KEY,
    channel TEXT,
    msg_ts TEXT UNIQUE,
    kind TEXT,
    title TEXT,
    status TEXT,
    urgency TEXT,
    team TEXT,
    responder TEXT,
    servidor TEXT,
    evento TEXT,
    descricao TEXT,
    inc TEXT,
    origem TEXT,
    team_tag TEXT,
    dc TEXT,
    monitor_id TEXT,
    monitor_group TEXT,
    requested_by TEXT,
    justificativa TEXT,
    last_triggered_at TEXT,
    edited_ts REAL,
    reply_count INTEGER DEFAULT 0,
    reactions_json TEXT,
    raw_json TEXT,
    first_seen REAL,
    scanned_at REAL
);
CREATE INDEX IF NOT EXISTS ix_pages_msg_ts ON pages(msg_ts);
CREATE INDEX IF NOT EXISTS ix_pages_inc ON pages(inc);

CREATE TABLE IF NOT EXISTS transitions (
    id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    responder TEXT,
    event_ts REAL NOT NULL,
    edited_ts REAL,
    source TEXT NOT NULL CHECK(source IN ('live', 'history')),
    raw_json TEXT,
    UNIQUE(page_id, status, source)
);

CREATE TABLE IF NOT EXISTS human_events (
    id INTEGER PRIMARY KEY,
    page_id INTEGER,
    msg_ts TEXT,
    event_ts REAL NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('reply', 'channel_msg', 'reaction')),
    user TEXT NOT NULL,
    text TEXT,
    attribution TEXT,
    UNIQUE(kind, event_ts, user)
);
CREATE INDEX IF NOT EXISTS ix_human_page ON human_events(page_id);

CREATE TABLE IF NOT EXISTS handovers (
    date TEXT NOT NULL,
    schedule TEXT NOT NULL,
    user TEXT,
    name TEXT,
    msg_ts TEXT,
    PRIMARY KEY(date, schedule)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    window_start REAL,
    window_end REAL,
    kind TEXT,
    html_path TEXT,
    pdf_path TEXT,
    json_path TEXT,
    sent_to TEXT,
    sent_ts TEXT,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

PAGE_COLS = (
    "page_id",
    "channel",
    "msg_ts",
    "kind",
    "title",
    "status",
    "urgency",
    "team",
    "responder",
    "servidor",
    "evento",
    "descricao",
    "inc",
    "origem",
    "team_tag",
    "dc",
    "monitor_id",
    "monitor_group",
    "requested_by",
    "justificativa",
    "last_triggered_at",
    "edited_ts",
    "reply_count",
    "reactions_json",
    "raw_json",
    "first_seen",
    "scanned_at",
)


@dataclass
class PageRow:
    page_id: int
    channel: str | None
    msg_ts: str
    kind: str
    title: str | None
    status: str | None
    urgency: str | None
    team: str | None
    responder: str | None
    servidor: str | None
    evento: str | None
    descricao: str | None
    inc: str | None
    origem: str | None
    team_tag: str | None
    dc: str | None
    monitor_id: str | None
    monitor_group: str | None
    requested_by: str | None
    justificativa: str | None
    last_triggered_at: str | None
    edited_ts: float | None
    reply_count: int
    reactions: list[dict]
    first_seen: float | None
    scanned_at: float | None

    @property
    def t0(self) -> float:
        return float(self.msg_ts)

    @property
    def page_url(self) -> str:
        return f"https://app.datadoghq.com/on-call/pages/{self.page_id}"


@dataclass
class TransitionRow:
    page_id: int
    status: str
    responder: str | None
    event_ts: float
    edited_ts: float | None
    source: str


@dataclass
class HumanEventRow:
    page_id: int | None
    msg_ts: str | None
    event_ts: float
    kind: str
    user: str
    text: str | None
    attribution: str | None


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # o bot (slack_bolt) chama o store de threads de trabalho: uma conexão
        # compartilhada, serializada por lock (autocommit + WAL)
        raw = sqlite3.connect(
            str(self.path), timeout=5.0, isolation_level=None, check_same_thread=False
        )
        raw.row_factory = sqlite3.Row
        self.conn = _LockedConn(raw)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.migrate()

    def migrate(self) -> None:
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------------ pages
    def upsert_page(self, page: dict, msg: dict, channel: str, scanned_at: float) -> None:
        """``page`` = saída de parse_datadog_page; ``msg`` = mensagem crua do Slack."""
        edited = msg.get("edited") or {}
        edited_ts = float(edited["ts"]) if edited.get("ts") else None
        row = {k: page.get(k) for k in PAGE_COLS if k in page}
        row.update(
            channel=channel,
            msg_ts=msg["ts"],
            edited_ts=edited_ts,
            reply_count=int(msg.get("reply_count") or 0),
            reactions_json=json.dumps(msg.get("reactions") or [], ensure_ascii=False),
            raw_json=json.dumps(msg, ensure_ascii=False),
            scanned_at=scanned_at,
        )
        cols = [c for c in PAGE_COLS if c in row]
        placeholders = ", ".join("?" for _ in cols)
        updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c not in ("page_id", "first_seen"))
        self.conn.execute(
            f"INSERT INTO pages ({', '.join(cols)}, first_seen) VALUES ({placeholders}, ?) "
            f"ON CONFLICT(page_id) DO UPDATE SET {updates}",
            [row[c] for c in cols] + [scanned_at],
        )

    def update_page_state(
        self, page_id: int, status: str | None, responder: str | None, edited_ts: float | None
    ) -> None:
        self.conn.execute(
            "UPDATE pages SET status=COALESCE(?, status), responder=COALESCE(?, responder), "
            "edited_ts=COALESCE(?, edited_ts) WHERE page_id=?",
            (status, responder, edited_ts, page_id),
        )

    def bump_reply_count(self, page_id: int) -> None:
        self.conn.execute("UPDATE pages SET reply_count=reply_count+1 WHERE page_id=?", (page_id,))

    @staticmethod
    def _row_to_page(r: sqlite3.Row) -> PageRow:
        return PageRow(
            page_id=r["page_id"],
            channel=r["channel"],
            msg_ts=r["msg_ts"],
            kind=r["kind"] or "auto",
            title=r["title"],
            status=r["status"],
            urgency=r["urgency"],
            team=r["team"],
            responder=r["responder"],
            servidor=r["servidor"],
            evento=r["evento"],
            descricao=r["descricao"],
            inc=r["inc"],
            origem=r["origem"],
            team_tag=r["team_tag"],
            dc=r["dc"],
            monitor_id=r["monitor_id"],
            monitor_group=r["monitor_group"],
            requested_by=r["requested_by"],
            justificativa=r["justificativa"],
            last_triggered_at=r["last_triggered_at"],
            edited_ts=r["edited_ts"],
            reply_count=r["reply_count"] or 0,
            reactions=json.loads(r["reactions_json"] or "[]"),
            first_seen=r["first_seen"],
            scanned_at=r["scanned_at"],
        )

    def pages_between(self, start: float, end: float) -> list[PageRow]:
        """Pages com t0 em [start, end), mais antigas primeiro."""
        rows = self.conn.execute(
            "SELECT * FROM pages WHERE CAST(msg_ts AS REAL) >= ? AND CAST(msg_ts AS REAL) < ? "
            "ORDER BY CAST(msg_ts AS REAL)",
            (start, end),
        ).fetchall()
        return [self._row_to_page(r) for r in rows]

    def page_by_msg_ts(self, msg_ts: str) -> PageRow | None:
        r = self.conn.execute("SELECT * FROM pages WHERE msg_ts=?", (msg_ts,)).fetchone()
        return self._row_to_page(r) if r else None

    def find_page(self, ident: str) -> PageRow | None:
        """Por ``#52488`` / ``52488`` (page_id) ou por INC (``INC13450``, ``21714051``)."""
        s = ident.strip().lstrip("#")
        if s.isdigit():
            r = self.conn.execute("SELECT * FROM pages WHERE page_id=?", (int(s),)).fetchone()
            if r:
                return self._row_to_page(r)
        r = self.conn.execute(
            "SELECT * FROM pages WHERE UPPER(inc)=UPPER(?) ORDER BY CAST(msg_ts AS REAL) DESC LIMIT 1",  # noqa: E501
            (s,),
        ).fetchone()
        return self._row_to_page(r) if r else None

    def pages_by_inc(self, inc: str) -> list[PageRow]:
        rows = self.conn.execute(
            "SELECT * FROM pages WHERE UPPER(inc)=UPPER(?) ORDER BY CAST(msg_ts AS REAL)", (inc,)
        ).fetchall()
        return [self._row_to_page(r) for r in rows]

    def last_page_ts(self) -> float | None:
        r = self.conn.execute("SELECT MAX(CAST(msg_ts AS REAL)) AS m FROM pages").fetchone()
        return float(r["m"]) if r and r["m"] is not None else None

    # ------------------------------------------------------------ transitions
    def add_transition(
        self,
        page_id: int,
        status: str,
        responder: str | None,
        event_ts: float,
        edited_ts: float | None,
        source: str,
        raw: dict | None = None,
    ) -> bool:
        """Insere se ainda não existir (page_id, status, source). Uma transição
        'history' NUNCA é inserida se já houver a 'live' equivalente."""
        if source == "history":
            live = self.conn.execute(
                "SELECT 1 FROM transitions WHERE page_id=? AND status=? AND source='live'",
                (page_id, status),
            ).fetchone()
            if live:
                return False
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO transitions (page_id, status, responder, event_ts, edited_ts, "
            "source, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                page_id,
                status,
                responder,
                event_ts,
                edited_ts,
                source,
                json.dumps(raw, ensure_ascii=False) if raw else None,
            ),
        )
        return cur.rowcount > 0

    def transitions_for(self, page_ids: list[int]) -> dict[int, list[TransitionRow]]:
        if not page_ids:
            return {}
        out: dict[int, list[TransitionRow]] = {}
        for chunk in _chunks(page_ids, 500):
            q = ",".join("?" for _ in chunk)
            rows = self.conn.execute(
                f"SELECT * FROM transitions WHERE page_id IN ({q}) ORDER BY event_ts", chunk
            ).fetchall()
            for r in rows:
                out.setdefault(r["page_id"], []).append(
                    TransitionRow(
                        r["page_id"],
                        r["status"],
                        r["responder"],
                        r["event_ts"],
                        r["edited_ts"],
                        r["source"],
                    )
                )
        return out

    def last_live_event_ts(self) -> float | None:
        r = self.conn.execute(
            "SELECT MAX(event_ts) AS m FROM transitions WHERE source='live'"
        ).fetchone()
        return float(r["m"]) if r and r["m"] is not None else None

    # ----------------------------------------------------------- human events
    def add_human_event(
        self,
        page_id: int | None,
        msg_ts: str | None,
        event_ts: float,
        kind: str,
        user: str,
        text: str | None,
        attribution: str | None,
    ) -> bool:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO human_events (page_id, msg_ts, event_ts, kind, user, text, "
            "attribution) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (page_id, msg_ts, event_ts, kind, user, text, attribution),
        )
        return cur.rowcount > 0

    def human_events_for(self, page_ids: list[int]) -> dict[int, list[HumanEventRow]]:
        if not page_ids:
            return {}
        out: dict[int, list[HumanEventRow]] = {}
        for chunk in _chunks(page_ids, 500):
            q = ",".join("?" for _ in chunk)
            rows = self.conn.execute(
                f"SELECT * FROM human_events WHERE page_id IN ({q}) ORDER BY event_ts", chunk
            ).fetchall()
            for r in rows:
                out.setdefault(r["page_id"], []).append(
                    HumanEventRow(
                        r["page_id"],
                        r["msg_ts"],
                        r["event_ts"],
                        r["kind"],
                        r["user"],
                        r["text"],
                        r["attribution"],
                    )
                )
        return out

    def unattributed_human_events(self, start: float, end: float) -> list[HumanEventRow]:
        rows = self.conn.execute(
            "SELECT * FROM human_events WHERE page_id IS NULL AND event_ts >= ? AND event_ts < ? "
            "ORDER BY event_ts",
            (start, end),
        ).fetchall()
        return [
            HumanEventRow(
                r["page_id"],
                r["msg_ts"],
                r["event_ts"],
                r["kind"],
                r["user"],
                r["text"],
                r["attribution"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------- recurrence
    def recurrence(self, since: float, until: float) -> dict[str, dict[str, int]]:
        """Contagens em [since, until) por alert_key (SERVIDOR|evento), inc e monitor."""
        rows = self.conn.execute(
            "SELECT servidor, evento, inc, monitor_id, monitor_group FROM pages "
            "WHERE CAST(msg_ts AS REAL) >= ? AND CAST(msg_ts AS REAL) < ?",
            (since, until),
        ).fetchall()
        by_alert: dict[str, int] = {}
        by_inc: dict[str, int] = {}
        by_mon: dict[str, int] = {}
        for r in rows:
            ak = alert_key(r["servidor"], r["evento"])
            if ak:
                by_alert[ak] = by_alert.get(ak, 0) + 1
            if r["inc"]:
                k = r["inc"].upper()
                by_inc[k] = by_inc.get(k, 0) + 1
            if r["monitor_id"]:
                k = f"{r['monitor_id']}|{r['monitor_group'] or ''}"
                by_mon[k] = by_mon.get(k, 0) + 1
        return {"alert": by_alert, "inc": by_inc, "monitor": by_mon}

    # -------------------------------------------------------------- handovers
    def upsert_handover(
        self, date: str, schedule: str, user: str | None, name: str | None, msg_ts: str
    ) -> None:
        self.conn.execute(
            "INSERT INTO handovers (date, schedule, user, name, msg_ts) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(date, schedule) DO UPDATE SET user=excluded.user, name=excluded.name, "
            "msg_ts=excluded.msg_ts",
            (date, schedule, user, name, msg_ts),
        )

    def latest_handover(self, before_ts: float | None = None) -> dict[str, dict]:
        """Último handover por schedule (opcionalmente anterior a ``before_ts``)."""
        out: dict[str, dict] = {}
        for sched in ("Interna", "Externa"):
            if before_ts is None:
                r = self.conn.execute(
                    "SELECT * FROM handovers WHERE schedule=? ORDER BY CAST(msg_ts AS REAL) DESC LIMIT 1",  # noqa: E501
                    (sched,),
                ).fetchone()
            else:
                r = self.conn.execute(
                    "SELECT * FROM handovers WHERE schedule=? AND CAST(msg_ts AS REAL) <= ? "
                    "ORDER BY CAST(msg_ts AS REAL) DESC LIMIT 1",
                    (sched, before_ts),
                ).fetchone()
            if r:
                out[sched] = {
                    "user": r["user"],
                    "name": r["name"],
                    "date": r["date"],
                    "msg_ts": r["msg_ts"],
                }
        return out

    def last_handover_with_user(self, schedule: str, before_ts: float | None = None) -> dict | None:
        q = "SELECT * FROM handovers WHERE schedule=? AND user IS NOT NULL"
        args: list = [schedule]
        if before_ts is not None:
            q += " AND CAST(msg_ts AS REAL) <= ?"
            args.append(before_ts)
        r = self.conn.execute(q + " ORDER BY CAST(msg_ts AS REAL) DESC LIMIT 1", args).fetchone()
        return dict(r) if r else None

    # ---------------------------------------------------------------- reports
    def add_report(
        self,
        window_start: float,
        window_end: float,
        kind: str,
        html_path: str | None,
        pdf_path: str | None,
        json_path: str | None,
        sent_to: str | None,
        sent_ts: str | None,
        created_at: float,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO reports (window_start, window_end, kind, html_path, pdf_path, json_path, "
            "sent_to, sent_ts, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                window_start,
                window_end,
                kind,
                html_path,
                pdf_path,
                json_path,
                sent_to,
                sent_ts,
                created_at,
            ),
        )
        return int(cur.lastrowid)

    def last_report(self, kind: str | None = None, with_pdf: bool = True) -> dict | None:
        q = "SELECT * FROM reports WHERE 1=1"
        args: list = []
        if kind:
            q += " AND kind=?"
            args.append(kind)
        if with_pdf:
            q += " AND pdf_path IS NOT NULL"
        q += " ORDER BY created_at DESC LIMIT 1"
        r = self.conn.execute(q, args).fetchone()
        return dict(r) if r else None

    # ------------------------------------------------------------------ users
    def user_name(self, user_id: str) -> str | None:
        r = self.conn.execute("SELECT name FROM users WHERE user_id=?", (user_id,)).fetchone()
        return r["name"] if r else None

    def set_user_name(self, user_id: str, name: str, now: float | None = None) -> None:
        import time as _t

        now = _t.time() if now is None else now
        self.conn.execute(
            "INSERT INTO users (user_id, name, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at",
            (user_id, name, now),
        )

    def user_names(self) -> dict[str, str]:
        return {r["user_id"]: r["name"] for r in self.conn.execute("SELECT * FROM users")}

    # ------------------------------------------------------------------- meta
    def get_meta(self, key: str) -> str | None:
        r = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r["value"] if r else None

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


class _LockedConn:
    """Serializa o acesso a uma sqlite3.Connection entre threads."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._lock = threading.RLock()

    def execute(self, sql: str, params=()):
        with self._lock:
            cur = self._conn.execute(sql, params)
            # materializa o cursor dentro do lock para não vazar iteração concorrente
            return _Result(cur)

    def executescript(self, sql: str) -> None:
        with self._lock:
            self._conn.executescript(sql)

    def close(self) -> None:
        with self._lock:
            self._conn.close()


class _Result:
    def __init__(self, cur: sqlite3.Cursor):
        self.rowcount = cur.rowcount
        self.lastrowid = cur.lastrowid
        self._rows = cur.fetchall() if cur.description else []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __iter__(self):
        return iter(self._rows)


def alert_key(servidor: str | None, evento: str | None) -> str | None:
    if not servidor and not evento:
        return None
    s = (servidor or "?").strip().upper()
    e = " ".join((evento or "?").split())
    return f"{s}|{e}"


def _chunks(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]

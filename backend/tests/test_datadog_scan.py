"""Scan do histórico com um cliente Slack falso (sem rede)."""

from app.corvo.datadog_scan import scan_channel
from app.corvo.datadog_store import Store
from tests.test_datadog_parse import AUTO, FLOAT_IP, HANDOVER, MANUAL

T_AUTO = float(AUTO["ts"])


class FakeClient:
    def __init__(self, history, replies=None):
        self._history = history
        self._replies = replies or {}
        self.calls = []

    def conversations_history(self, **kw):
        self.calls.append(("history", kw))
        lo, hi = float(kw["oldest"]), float(kw.get("latest") or 9e9)
        msgs = [m for m in self._history if lo <= float(m["ts"]) <= hi]
        return {"messages": msgs, "response_metadata": {}}

    def conversations_replies(self, **kw):
        self.calls.append(("replies", kw))
        parent = [m for m in self._history if m["ts"] == kw["ts"]]
        return {"messages": parent + self._replies.get(kw["ts"], []), "response_metadata": {}}

    def users_info(self, user):
        self.calls.append(("users_info", user))
        return {"user": {"real_name": f"Nome {user}", "profile": {}}}


def _hist():
    auto = {**AUTO, "reply_count": 2, "edited": {"ts": f"{T_AUTO + 900:.6f}"}}
    human_channel = {"user": "UH2", "ts": f"{T_AUTO + 300:.6f}", "text": "Analisando o leaf"}
    join = {"user": "UX", "ts": f"{T_AUTO + 10:.6f}", "subtype": "channel_join", "text": "joined"}
    return [HANDOVER, MANUAL, FLOAT_IP, auto, human_channel, join]


def test_scan_popula_store(tmp_path):
    replies = {
        AUTO["ts"]: [
            {
                "user": "UH",
                "ts": f"{T_AUTO + 60:.6f}",
                "text": "Analisando",
                "thread_ts": AUTO["ts"],
            },
            {"user": "U07Q4UQU0GM", "bot_id": "B1", "ts": f"{T_AUTO + 70:.6f}", "text": "bot"},
        ]
    }
    client = FakeClient(_hist(), replies)
    store = Store(tmp_path / "s.sqlite")
    res = scan_channel(client, store, "C1", oldest=0, sleep=0)

    assert res.pages == 3 and res.pages_new == 3
    assert res.handovers == 1
    assert res.replies_fetched == 1
    assert res.human_msgs == 1
    assert res.unparsed_bot_msgs == []

    pages = {p.page_id: p for p in store.pages_between(0, 9e9)}
    assert set(pages) == {52488, 52481, 52477}
    assert pages[52488].edited_ts == T_AUTO + 900
    assert pages[52488].dc == "TESP03"

    tr = store.transitions_for([52488])[52488]
    assert [(t.status, t.source) for t in tr] == [("Triggered", "history"), ("Resolved", "history")]
    assert tr[1].event_ts == T_AUTO + 900

    ev = store.human_events_for([52488])[52488]
    assert [(e.kind, e.user, e.attribution) for e in ev] == [("reply", "UH", "thread")]
    # mensagem humana do canal 5 min após a page 52488, que já tem resposta na
    # thread e é a única recente: fica sem atribuição (não inventa vínculo)
    un = store.unattributed_human_events(0, 9e9)
    assert [(e.kind, e.user, e.text) for e in un] == [("channel_msg", "UH2", "Analisando o leaf")]

    h = store.latest_handover()
    assert h["Interna"]["user"] == "U08D079PFST" and h["Interna"]["name"] == "Junovan Fantin"
    assert store.user_name("U053RFRVBE1") == "Max Ferreira"
    assert store.user_name("UH") == "Nome UH"
    assert store.get_meta("last_scan_at")


def test_scan_idempotente_e_live_preservado(tmp_path):
    client = FakeClient(_hist())
    store = Store(tmp_path / "s.sqlite")
    store.upsert_page({"page_id": 52488, "kind": "auto"}, {"ts": AUTO["ts"]}, "C1", 1.0)
    store.add_transition(52488, "Acknowledged", "U08D079PFST", T_AUTO + 100, None, "live")
    res = scan_channel(client, store, "C1", oldest=0, fetch_replies=False, sleep=0)
    assert res.pages == 3 and res.pages_new == 2
    res2 = scan_channel(client, store, "C1", oldest=0, fetch_replies=False, sleep=0)
    assert res2.pages_new == 0
    tr = store.transitions_for([52488])[52488]
    assert ("Acknowledged", "live") in [(t.status, t.source) for t in tr]
    assert len(store.pages_between(0, 9e9)) == 3

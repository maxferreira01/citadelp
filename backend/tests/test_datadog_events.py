"""Eventos ao vivo (Socket Mode) → store, via apply_event (puro)."""

from app.corvo.bot_app import apply_event
from app.corvo.datadog_store import Store
from tests.test_datadog_parse import AUTO, HANDOVER

CH = "C087SV98MBM"
DD = "U07Q4UQU0GM"
T0 = float(AUTO["ts"])


def _att(status, responder=None):
    a = dict(AUTO["attachments"][0])
    a["text"] = a["text"].replace(":white_check_mark: Resolved", status)
    if responder is None:
        a["text"] = a["text"].replace("*Responder:*\n<@U08D079PFST>\n", "")
    return [a]


def _new_page_event(status="Triggered"):
    return {
        "type": "message",
        "channel": CH,
        "user": DD,
        "bot_id": "B1",
        "ts": AUTO["ts"],
        "attachments": _att(status),
    }


def _changed(old_status, new_status, responder="U08D079PFST", edited_ts=None, event_ts=None):
    return {
        "type": "message",
        "subtype": "message_changed",
        "channel": CH,
        "event_ts": f"{event_ts or T0 + 120:.6f}",
        "ts": f"{event_ts or T0 + 120:.6f}",
        "message": {
            "user": DD,
            "bot_id": "B1",
            "ts": AUTO["ts"],
            "attachments": _att(new_status, responder),
            "edited": {"user": DD, "ts": f"{edited_ts or T0 + 120:.6f}"},
        },
        "previous_message": {
            "user": DD,
            "bot_id": "B1",
            "ts": AUTO["ts"],
            "attachments": _att(old_status, None),
        },
    }


def test_ciclo_de_vida_da_page(tmp_path):
    st = Store(tmp_path / "e.sqlite")
    assert apply_event(st, _new_page_event(), CH, DD) == "page"
    p = st.page_by_msg_ts(AUTO["ts"])
    assert p.page_id == 52488 and p.status == "Triggered" and p.responder is None

    assert (
        apply_event(st, _changed("Triggered", "Acknowledged", event_ts=T0 + 90), CH, DD)
        == "transition:Triggered->Acknowledged"
    )
    assert (
        apply_event(st, _changed("Acknowledged", "Acknowledged", event_ts=T0 + 91), CH, DD)
        == "changed_same_status"
    )
    assert (
        apply_event(st, _changed("Acknowledged", "Resolved", event_ts=T0 + 900), CH, DD)
        == "transition:Acknowledged->Resolved"
    )

    p = st.page_by_msg_ts(AUTO["ts"])
    assert p.status == "Resolved" and p.responder == "U08D079PFST"
    tr = st.transitions_for([52488])[52488]
    assert [(t.status, t.source, int(t.event_ts - T0)) for t in tr] == [
        ("Triggered", "live", 0),
        ("Acknowledged", "live", 90),
        ("Resolved", "live", 900),
    ]


def test_reply_reacao_e_mensagem_do_canal(tmp_path):
    st = Store(tmp_path / "e.sqlite")
    apply_event(st, _new_page_event(), CH, DD)
    ev = {
        "type": "message",
        "channel": CH,
        "user": "UH",
        "ts": f"{T0 + 60:.6f}",
        "thread_ts": AUTO["ts"],
        "text": "Analisando",
    }
    assert apply_event(st, ev, CH, DD) == "reply"
    assert st.page_by_msg_ts(AUTO["ts"]).reply_count == 1
    ev2 = {
        "type": "reaction_added",
        "user": "UH",
        "reaction": "eyes",
        "event_ts": f"{T0 + 30:.6f}",
        "item": {"type": "message", "channel": CH, "ts": AUTO["ts"]},
    }
    assert apply_event(st, ev2, CH, DD) == "reaction"
    ev3 = {
        "type": "message",
        "channel": CH,
        "user": "UH2",
        "ts": f"{T0 + 200:.6f}",
        "text": "olhando o LEAF1001TESP03",
    }
    assert apply_event(st, ev3, CH, DD) == "channel_msg:mention"
    kinds = [(e.kind, e.attribution) for e in st.human_events_for([52488])[52488]]
    assert sorted(kinds) == [
        ("channel_msg", "mention"),
        ("reaction", "reaction"),
        ("reply", "thread"),
    ]


def test_ignora_o_que_nao_interessa(tmp_path):
    st = Store(tmp_path / "e.sqlite")
    assert (
        apply_event(st, {"type": "message", "channel": "COUTRO", "user": "U1", "ts": "1.0"}, CH, DD)
        == "ignored"
    )
    assert (
        apply_event(
            st,
            {
                "type": "message",
                "channel": CH,
                "user": "U1",
                "ts": "1.0",
                "subtype": "channel_join",
            },
            CH,
            DD,
        )
        == "ignored"
    )
    assert (
        apply_event(
            st,
            {"type": "message", "channel": CH, "user": "UBOT", "ts": "1.0", "text": "eu"},
            CH,
            DD,
            self_user="UBOT",
        )
        == "ignored"
    )
    assert (
        apply_event(
            st,
            {
                "type": "reaction_added",
                "user": DD,
                "reaction": "x",
                "event_ts": "1.0",
                "item": {"type": "message", "channel": CH, "ts": "1.0"},
            },
            CH,
            DD,
        )
        == "ignored"
    )
    hv = {
        "type": "message",
        "channel": CH,
        "user": DD,
        "bot_id": "B1",
        "ts": HANDOVER["ts"],
        "text": HANDOVER["text"],
    }
    assert apply_event(st, hv, CH, DD) == "handover"
    assert st.latest_handover()["Externa"]["user"] == "U053RFRVBE1"

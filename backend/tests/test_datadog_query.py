from datetime import datetime, timedelta

from app.corvo.datadog_query import BRT, QueryEngine, anchor_08, daily_window, period
from app.corvo.datadog_store import Store

NOW = datetime(2026, 8, 28, 10, 30, tzinfo=BRT)


def test_period_janelas():
    a = anchor_08(NOW)
    assert a == datetime(2026, 8, 28, 8, 0, tzinfo=BRT)
    assert anchor_08(NOW.replace(hour=7)) == datetime(2026, 8, 27, 8, 0, tzinfo=BRT)
    s, e, _ = period("hoje", NOW)
    assert (s, e) == (a.timestamp(), NOW.timestamp())
    s, e, label = period("ontem", NOW)
    assert (s, e) == ((a - timedelta(days=1)).timestamp(), a.timestamp())
    assert label == "27/08 08:00 → 28/08 08:00"
    s, e, _ = period("mes", NOW)
    assert datetime.fromtimestamp(s, BRT) == datetime(2026, 8, 1, tzinfo=BRT)
    s, e, _ = period("mes_anterior", NOW)
    assert datetime.fromtimestamp(s, BRT) == datetime(2026, 7, 1, tzinfo=BRT)
    assert datetime.fromtimestamp(e, BRT) == datetime(2026, 8, 1, tzinfo=BRT)
    s, e, label = daily_window(NOW, 1)
    assert label == "27/08 08:00 → 28/08 08:00"
    s, e, label = period("4d", NOW)
    assert (e - s) == 4 * 86400 and label.startswith("últimos 4 dias")


def _seed(tmp_path):
    st = Store(tmp_path / "q.sqlite")
    a = anchor_08(NOW).timestamp()
    base = dict(
        kind="auto",
        title="t",
        status="Resolved",
        urgency="High",
        team="InfraOPS Redes",
        responder="UR",
        servidor="LEAF1001TESP03",
        evento="Interface Ethernet1/21",
        descricao=None,
        inc="1",
        origem="checkmk_redes",
        team_tag=None,
        dc="TESP03",
        monitor_id=None,
        monitor_group=None,
        requested_by=None,
        justificativa=None,
        last_triggered_at=None,
    )
    # 3 pages na janela de ontem: 2 iguais (recorrente), 1 manual sem resposta
    st.upsert_page(
        {**base, "page_id": 1},
        {"ts": f"{a - 20000:.6f}", "edited": {"ts": f"{a - 19000:.6f}"}},
        "C",
        1,
    )
    st.upsert_page({**base, "page_id": 2}, {"ts": f"{a - 10000:.6f}"}, "C", 1)
    st.upsert_page(
        {
            **base,
            "page_id": 3,
            "kind": "manual",
            "responder": None,
            "status": "Triggered",
            "servidor": None,
            "evento": None,
            "inc": "INC1",
            "dc": None,
            "requested_by": "x",
        },
        {"ts": f"{a - 5000:.6f}"},
        "C",
        1,
    )
    # 1 page de hoje (fora da janela de ontem)
    st.upsert_page(
        {**base, "page_id": 4, "dc": "TECE01", "servidor": "FW01TECE01"},
        {"ts": f"{a + 100:.6f}"},
        "C",
        1,
    )
    st.add_transition(1, "Acknowledged", "UR", a - 20000 + 60, None, "live")
    st.add_human_event(1, "x", a - 20000 + 120, "reply", "UH", "analisando", "thread")
    st.add_human_event(2, "y", a - 10000 + 600, "channel_msg", "UH", "olhando", "nearest")
    st.upsert_handover("2026-08-27", "Interna", "UI", "Interno", f"{a - 50000:.6f}")
    st.set_user_name("UR", "Responder")
    st.set_user_name("UH", "Humano")
    return st


def test_summary_ontem(tmp_path):
    q = QueryEngine(_seed(tmp_path))
    s, e, label = period("ontem", NOW)
    sm = q.summary(s, e, label)
    assert sm["total"] == 3
    assert sm["by_kind"] == {"auto": 2, "manual": 1}
    assert sm["by_dc"] == {"TESP03": 2, "?": 1}
    assert sm["response"]["n"] == 2 and sm["response"]["median"] == 360.0
    assert sm["ack_exact"] == {"n": 1, "median": 60.0, "p90": 60.0, "max": 60, "mean": 60.0}
    assert sm["ack_sources"] == {"live": 1, "proxy": 1, "none": 1}
    assert [p["page_id"] for p in sm["unanswered"]] == [3]
    assert sm["unanswered_pct"] == 33
    assert sm["recurrent_day"][0]["key"] == "LEAF1001TESP03|Interface Ethernet1/21"
    assert sm["recurrent_day"][0]["count"] == 2 and sm["recurrent_day"][0]["d30"] == 2
    assert sm["responders"][0] == {
        "user": "UR",
        "name": "Responder",
        "pages": 2,
        "silent_ack": 0,
        "response": {"n": 2, "median": 360.0, "p90": 600.0, "max": 600, "mean": 360.0},
    }
    assert sm["oncall"]["Interna"]["user"] == "UI" and sm["oncall"]["Externa"] is None
    assert len(sm["manual"]) == 1 and sm["manual"][0]["requested_by"] == "x"
    assert sm["pages"][0]["responder_name"] == "Responder"
    assert sm["pages"][0]["d7"] == 2


def test_consultas(tmp_path):
    q = QueryEngine(_seed(tmp_path))
    m = q.count_month(NOW)
    assert m["total"] == 4 and m["prev_total"] == 0
    assert m["by_dc"] == {"TESP03": 2, "TECE01": 1, "?": 1}
    s, e, _ = period("7d", NOW)
    assert q.top_dcs(s, e)[0] == {"dc": "TESP03", "count": 2, "pct": 50}
    assert q.recurrent(s, e)["alert"][0]["count"] == 2
    assert [p["page_id"] for p in q.unanswered(s, e)] == [3]
    rs = q.response_stats(s, e)
    assert rs["total"] == 4 and rs["unanswered"] == 1
    card = q.page_card("1")
    assert card["ack_source"] == "live" and card["timeline"][0]["status"] == "Acknowledged"
    assert card["events"][0]["name"] == "Humano"
    assert card["d30"] == 1 and card["same_inc"][0]["page_id"] == 1
    assert q.page_card("nada") is None
    assert q.oncall()["Interna"]["name"] == "Interno"


def test_oncall_vazio_mostra_ultimo(tmp_path):
    st = Store(tmp_path / "h.sqlite")
    st.upsert_handover("2026-08-27", "Externa", "UX", "Max", "1787864411.0")
    st.upsert_handover("2026-08-28", "Externa", None, None, "1787914807.0")
    oc = QueryEngine(st).oncall()
    assert oc["Externa"]["user"] is None
    assert oc["Externa"]["last"] == {"user": "UX", "name": "Max", "since": "2026-08-27"}
    assert oc["Interna"] is None

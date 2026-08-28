from app.corvo.datadog_store import Store, alert_key

PAGE = {
    "page_id": 52488,
    "title": "LEAF1001TESP03 Interface Ethernet1/21",
    "kind": "auto",
    "status": "Resolved",
    "urgency": "High",
    "team": "InfraOPS Redes",
    "responder": "U08D079PFST",
    "servidor": "LEAF1001TESP03",
    "evento": "Interface Ethernet1/21",
    "descricao": "x",
    "inc": "21714051",
    "origem": "checkmk_redes",
    "team_tag": "infra_redes",
    "dc": "TESP03",
    "monitor_id": "162116916",
    "monitor_group": "cherwellincidentid:21714051",
    "requested_by": None,
    "justificativa": None,
    "last_triggered_at": None,
}
MSG = {
    "ts": "1787891648.678409",
    "reply_count": 2,
    "edited": {"ts": "1787892000.000000"},
    "reactions": [{"name": "eyes", "users": ["U1"]}],
}


def _store(tmp_path):
    return Store(tmp_path / "t.sqlite")


def test_migrate_idempotente(tmp_path):
    s = _store(tmp_path)
    s.migrate()
    s.migrate()
    assert s.conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0] == 0


def test_upsert_nao_duplica_e_preserva_first_seen(tmp_path):
    s = _store(tmp_path)
    s.upsert_page(PAGE, MSG, "C1", scanned_at=100.0)
    s.upsert_page({**PAGE, "status": "Triggered"}, MSG, "C1", scanned_at=200.0)
    rows = s.pages_between(0, 2e9)
    assert len(rows) == 1
    p = rows[0]
    assert p.status == "Triggered"
    assert p.first_seen == 100.0
    assert p.scanned_at == 200.0
    assert p.edited_ts == 1787892000.0
    assert p.reply_count == 2
    assert p.reactions[0]["name"] == "eyes"
    assert p.dc == "TESP03"


def test_find_page_por_id_e_inc(tmp_path):
    s = _store(tmp_path)
    s.upsert_page(PAGE, MSG, "C1", 1.0)
    assert s.find_page("#52488").page_id == 52488
    assert s.find_page("52488").page_id == 52488
    assert s.find_page("21714051").page_id == 52488
    assert s.find_page("inc99") is None


def test_transicao_history_nao_sobrescreve_live(tmp_path):
    s = _store(tmp_path)
    s.upsert_page(PAGE, MSG, "C1", 1.0)
    assert s.add_transition(52488, "Acknowledged", "U1", 1787891700.0, None, "live")
    assert not s.add_transition(52488, "Acknowledged", "U1", 1787891700.0, None, "live")
    assert not s.add_transition(52488, "Acknowledged", "U1", 1787892000.0, None, "history")
    assert s.add_transition(52488, "Resolved", "U1", 1787892000.0, 1787892000.0, "history")
    t = s.transitions_for([52488])[52488]
    assert [(x.status, x.source) for x in t] == [("Acknowledged", "live"), ("Resolved", "history")]
    assert s.last_live_event_ts() == 1787891700.0


def test_human_events_e_recorrencia(tmp_path):
    s = _store(tmp_path)
    s.upsert_page(PAGE, MSG, "C1", 1.0)
    s.upsert_page({**PAGE, "page_id": 52490}, {**MSG, "ts": "1787895000.000000"}, "C1", 1.0)
    s.upsert_page(
        {**PAGE, "page_id": 52491, "servidor": "FW01TECE01", "evento": "CPU", "inc": "1"},
        {**MSG, "ts": "1787896000.000000"},
        "C1",
        1.0,
    )
    assert s.add_human_event(
        52488, "1787891700.1", 1787891700.1, "reply", "U2", "Analisando", "thread"
    )
    assert not s.add_human_event(
        52488, "1787891700.1", 1787891700.1, "reply", "U2", "dup", "thread"
    )
    ev = s.human_events_for([52488])[52488]
    assert len(ev) == 1 and ev[0].user == "U2"
    rec = s.recurrence(0, 2e9)
    assert rec["alert"][alert_key("LEAF1001TESP03", "Interface Ethernet1/21")] == 2
    assert rec["inc"]["21714051"] == 2
    assert rec["alert"]["FW01TECE01|CPU"] == 1


def test_handover_e_reports(tmp_path):
    s = _store(tmp_path)
    s.upsert_handover("2026-08-27", "Interna", "U08D079PFST", "Junovan", "1787864411.674799")
    s.upsert_handover("2026-08-27", "Externa", "U053RFRVBE1", "Max", "1787864411.674799")
    s.upsert_handover("2026-08-28", "Externa", "U9", "Outro", "1787950811.000000")
    h = s.latest_handover()
    assert h["Interna"]["user"] == "U08D079PFST"
    assert h["Externa"]["user"] == "U9"
    assert s.latest_handover(before_ts=1787900000.0)["Externa"]["user"] == "U053RFRVBE1"
    assert s.last_report() is None
    s.add_report(1.0, 2.0, "daily", "a.html", None, "a.json", None, None, 10.0)
    s.add_report(1.0, 2.0, "daily", "b.html", "b.pdf", "b.json", "U3", "x", 20.0)
    assert s.last_report()["pdf_path"] == "b.pdf"
    assert s.last_report(with_pdf=False)["html_path"] == "b.html"


def test_users_e_meta(tmp_path):
    s = _store(tmp_path)
    assert s.user_name("U1") is None
    s.set_user_name("U1", "Fulano", 1.0)
    assert s.user_name("U1") == "Fulano"
    s.set_meta("last_scan", "123")
    assert s.get_meta("last_scan") == "123"

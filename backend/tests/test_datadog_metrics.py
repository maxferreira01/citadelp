from app.corvo.datadog_metrics import (
    PageRef,
    attribute_channel_message,
    compute_page_times,
    fmt_duration,
    histogram,
    median,
    percentile,
    stats,
)
from app.corvo.datadog_store import HumanEventRow, PageRow, TransitionRow

T0 = 1000.0


def _page(**kw) -> PageRow:
    base = dict(
        page_id=1,
        channel="C",
        msg_ts=f"{T0:.6f}",
        kind="auto",
        title="t",
        status="Resolved",
        urgency="High",
        team="InfraOPS Redes",
        responder="UR",
        servidor="H",
        evento="E",
        descricao=None,
        inc="1",
        origem=None,
        team_tag=None,
        dc="TESP03",
        monitor_id=None,
        monitor_group=None,
        requested_by=None,
        justificativa=None,
        last_triggered_at=None,
        edited_ts=None,
        reply_count=0,
        reactions=[],
        first_seen=None,
        scanned_at=None,
    )
    base.update(kw)
    return PageRow(**base)


def _ev(kind, ts, user="UH", attribution="thread"):
    return HumanEventRow(1, None, ts, kind, user, "txt", attribution)


def test_ack_live_vence_tudo():
    p = _page(status="Resolved", edited_ts=T0 + 900)
    tr = [
        TransitionRow(1, "Acknowledged", "UR", T0 + 120, None, "live"),
        TransitionRow(1, "Resolved", "UR", T0 + 800, None, "live"),
    ]
    t = compute_page_times(p, tr, [_ev("reply", T0 + 300)])
    assert (t.ack_s, t.ack_source) == (120, "live")
    assert (t.resolve_s, t.resolve_source) == (800, "live")
    assert t.response_s == 300 and t.response_user == "UH"
    assert t.first_touch_s == 120
    assert not t.unanswered and not t.silent_ack


def test_ack_por_edited_ts_quando_ainda_acknowledged():
    p = _page(status="Acknowledged", edited_ts=T0 + 200)
    t = compute_page_times(p, [], [])
    assert (t.ack_s, t.ack_source) == (200, "edited_ts")
    assert t.resolve_s is None
    assert t.first_touch_s == 200
    assert t.silent_ack  # responder sem sinal humano no Slack


def test_ack_proxy_quando_resolved_sem_live():
    p = _page(status="Resolved", edited_ts=T0 + 900)
    t = compute_page_times(p, [], [_ev("reply", T0 + 300)])
    assert (t.ack_s, t.ack_source) == (300, "proxy")
    assert (t.resolve_s, t.resolve_source) == (900, "edited_ts")
    assert t.first_touch_s == 300  # proxy não conta como toque exato, mas a resposta sim


def test_unanswered_e_reacao():
    p = _page(status="Triggered", responder=None)
    t = compute_page_times(p, [], [])
    assert t.unanswered and t.ack_s is None and t.first_touch_s is None
    t2 = compute_page_times(p, [], [_ev("reaction", T0 + 45)])
    assert t2.reaction_s == 45 and t2.first_touch_s == 45 and not t2.unanswered and t2.reacted


def test_atribuicao_de_mensagem_do_canal():
    pages = [
        PageRef(52488, T0, "LEAF1001TESP03", "21714051"),
        PageRef(52490, T0 + 600, "FW01TECE01", "INC13450"),
    ]
    assert attribute_channel_message(T0 + 700, "olhando o #52488", pages, set()) == (
        52488,
        "mention",
    )
    assert attribute_channel_message(T0 + 700, "fw01tece01 estável", pages, set()) == (
        52490,
        "mention",
    )
    assert attribute_channel_message(T0 + 700, "INC13450 fechado", pages, set()) == (
        52490,
        "mention",
    )
    assert attribute_channel_message(T0 + 700, "analisando", pages, set()) == (52490, "nearest")
    assert attribute_channel_message(T0 + 700, "analisando", pages, {52490}) == (52488, "nearest")
    assert attribute_channel_message(T0 + 700, "analisando", pages, {52488, 52490}) == (None, None)
    assert attribute_channel_message(T0 + 5000, "analisando", pages, set()) == (None, None)


def test_agregados():
    assert median([]) is None
    assert median([5]) == 5
    assert median([1, 2, 3, 4]) == 2.5
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 90) == 9
    assert percentile([7], 90) == 7
    s = stats([10, None, 30])
    assert s == {"n": 2, "median": 20.0, "p90": 30.0, "max": 30, "mean": 20.0}
    h = histogram([10, 400, None, 5000])
    assert [x["count"] for x in h] == [1, 1, 0, 0, 1, 1]
    assert fmt_duration(None) == "—"
    assert fmt_duration(45) == "45s"
    assert fmt_duration(252) == "4m12s"
    assert fmt_duration(3900) == "1h05"
    assert fmt_duration(90000) == "1d01h"

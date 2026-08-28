from datetime import datetime
from pathlib import Path

from app.corvo.bot import Command, handle, is_allowed, normalize, route, summary_blocks
from app.corvo.datadog_query import BRT, QueryEngine, anchor_08
from app.corvo.datadog_store import Store

NOW = datetime(2026, 8, 28, 10, 30, tzinfo=BRT)


def test_normalize():
    assert normalize("<@U123|Corvo> Tempo Médio, 30d!") == "tempo medio 30d"
    assert normalize("") == ""


def test_route_comandos():
    assert route("ajuda").name == "ajuda"
    assert route("").name == "ajuda"
    assert route("hoje") == Command("resumo", period="hoje", raw="hoje")
    assert route("Ontem").period == "ontem"
    assert route("7d").period == "7d"
    assert route("resumo 30 dias").period == "30d"
    assert route("4 dias").period == "4d" and route("4 dias").name == "resumo"
    assert route("14d").period == "14d"
    assert route("tempo medio 90 dias").period == "90d"
    assert route("1 dia").period == "ontem"
    assert route("quero relatório") == Command("resumo", period="hoje", raw="quero relatório")
    assert route("Me de um relatorio do dia.").period == "hoje"
    assert route("relatório de 7 dias").period == "7d"
    assert route("manda o relatório").name == "reenviar"
    assert route("4 dias").period == "4d" and route("4 dias").name == "resumo"
    assert route("14d").period == "14d"
    assert route("tempo medio 90 dias").period == "90d"
    assert route("1 dia").period == "ontem"
    assert route("quem está de plantão?").name == "plantao"
    assert route("plantão").name == "plantao"
    assert route("quem").name == "plantao"
    assert route("mês").name == "mes"
    assert route("quantos chamados temos no mês?").name == "mes"
    c = route("tempo médio 30d")
    assert (c.name, c.period) == ("tempo", "30d")
    assert route("qual o tempo de resposta?").name == "tempo"
    c = route("top dc mês")
    assert (c.name, c.period) == ("topdc", "mes")
    assert route("datacenters").name == "topdc"
    assert route("recorrentes 7d") == Command("recorrentes", period="7d", raw="recorrentes 7d")
    assert route("sem resposta").name == "semresposta"
    assert route("alerta 52488").arg == "52488"
    assert route("alerta #52488").arg == "52488"
    assert route("page INC13450").arg == "inc13450"
    assert route("reenviar pdf").name == "reenviar"
    assert route("manda o relatório").name == "reenviar"
    assert route("pdf").name == "reenviar"
    x = route("bom dia, tudo bem?")
    assert x.name == "ajuda" and x.arg == "bom dia tudo bem?"


def test_is_allowed():
    assert is_allowed("U1", ["U1", "U2"])
    assert not is_allowed("U3", ["U1"])
    assert is_allowed("U3", [])


class Ctx:
    def __init__(self, store):
        self.engine = QueryEngine(store)
        self.pdf_calls = []

    def render_pdf_for(self, kind, now):
        self.pdf_calls.append(kind)
        return Path("/tmp/x.pdf")

    def last_pdf(self):
        return None


def _seed(tmp_path):
    st = Store(tmp_path / "b.sqlite")
    a = anchor_08(NOW).timestamp()
    base = dict(
        kind="auto",
        title="LEAF1001TESP03 Interface Ethernet1/21",
        status="Resolved",
        urgency="High",
        team="InfraOPS Redes",
        responder="UR",
        servidor="LEAF1001TESP03",
        evento="Interface Ethernet1/21",
        inc="21714051",
        origem="checkmk_redes",
        dc="TESP03",
    )
    st.upsert_page({**base, "page_id": 52488}, {"ts": f"{a - 3600:.6f}"}, "C", 1)
    st.upsert_page(
        {**base, "page_id": 52489, "responder": None, "status": "Triggered"},
        {"ts": f"{a + 600:.6f}"},
        "C",
        1,
    )
    st.add_human_event(52488, "x", a - 3600 + 240, "reply", "UH", "Analisando", "thread")
    st.upsert_handover("2026-08-27", "Externa", "UX", "Max Ferreira", f"{a - 50000:.6f}")
    st.set_user_name("UR", "Junovan")
    st.set_user_name("UH", "Max")
    return st


def _text(reply):
    return "\n".join(
        b["text"]["text"]
        for b in reply.blocks
        if b["type"] in ("section", "header") and "text" in b
    )


def _fields(reply):
    return "\n".join(
        f["text"] for b in reply.blocks if b["type"] == "section" for f in b.get("fields", [])
    )


def test_handle_todos_os_comandos(tmp_path):
    ctx = Ctx(_seed(tmp_path))
    r = handle(route("ajuda"), ctx, NOW)
    assert "Comandos do Corvo" in _text(r) and r.blocks[-1]["type"] == "actions"

    r = handle(route("ontem"), ctx, NOW)
    assert "Corvo · Datadog On-Call — 27/08 08:00 → 28/08 08:00" in _text(r)
    assert "*Pages*\n1 · 1 auto" in _fields(r)
    assert r.file == Path("/tmp/x.pdf") and ctx.pdf_calls == ["ontem"]

    r = handle(route("hoje"), ctx, NOW)
    assert "🔴 1 (100%)" in _fields(r)
    assert "#52489" in _text(r) and "sem resposta" in _text(r)

    r = handle(route("plantão"), ctx, NOW)
    t = _text(r)
    assert "Plantão Redes Externa:* Max Ferreira (<@UX>)" in t
    assert "Plantão Redes Interna:* _sem handover registrado_" in t

    r = handle(route("mês"), ctx, NOW)
    assert "*Chamados no mês de 08/2026" in _text(r) and "TESP03: 2" in _text(r)

    r = handle(route("tempo médio 7d"), ctx, NOW)
    assert "mediana 4m00s" in _text(r) and "*Sem resposta:* 1" in _text(r)

    r = handle(route("top dc"), ctx, NOW)
    assert "1. *TESP03* — 2 (100%)" in _text(r)

    r = handle(route("recorrentes"), ctx, NOW)
    assert "×2" in _text(r)

    r = handle(route("sem resposta"), ctx, NOW)
    assert "1 sem resposta" in _text(r) and "#52489" in _text(r)

    r = handle(route("alerta 52488"), ctx, NOW)
    t = _text(r)
    assert "Page #52488" in t and "Junovan" in t and "Max (reply, 4m00s)" in t
    assert "*Ack:* 4m00s (proxy)" in t

    r = handle(route("alerta INC13450"), ctx, NOW)
    assert "Não achei" in _text(r)

    r = handle(route("reenviar pdf"), ctx, NOW)
    assert "Ainda não há PDF" in _text(r)

    r = handle(route("xyz"), ctx, NOW)
    assert "Não entendi" in r.blocks[0]["elements"][0]["text"]


def test_summary_blocks_limites(tmp_path):
    q = QueryEngine(_seed(tmp_path))
    from app.corvo.datadog_query import period

    s, e, label = period("7d", NOW)
    blocks, text = summary_blocks(q.summary(s, e, label))
    assert blocks[0]["type"] == "header" and len(blocks) <= 12
    assert all(
        len(b["text"]["text"]) <= 3000 for b in blocks if b["type"] == "section" and "text" in b
    )
    assert all(
        len(f["text"]) <= 2000
        for b in blocks
        if b["type"] == "section"
        for f in b.get("fields", [])
    )
    assert text.startswith("Corvo · Datadog On-Call")
    assert all(el["value"] for el in blocks[-2]["elements"])

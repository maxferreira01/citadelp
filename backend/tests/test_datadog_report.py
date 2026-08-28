import json
from datetime import datetime

import pytest

from app.corvo.datadog_query import BRT, QueryEngine, period
from app.corvo.datadog_report import build_blocks, render_html, render_pdf, write_artifacts
from tests.test_datadog_bot import NOW, _seed

SECOES = [
    "Pages na janela",
    "Tempo até a primeira resposta humana",
    "Pages da janela",
    "Datacenters",
    "Recorrência",
    "Por responder",
    "Por time e urgência",
    "Acionamentos manuais",
    "Plantão",
    "Sem resposta",
    "Método.",
]


def _summary(tmp_path, kind="7d"):
    q = QueryEngine(_seed(tmp_path))
    s, e, label = period(kind, NOW)
    return q.summary(s, e, label)


def test_blocks_validos(tmp_path):
    blocks, text = build_blocks(_summary(tmp_path))
    assert blocks[0]["type"] == "header"
    assert text and len(text) <= 3000
    for b in blocks:
        assert b["type"] in ("header", "section", "actions", "context", "divider")


def test_html_tem_as_11_secoes(tmp_path):
    html = render_html(_summary(tmp_path), generated_at=datetime(2026, 8, 28, 8, 1, tzinfo=BRT))
    for s in SECOES:
        assert s in html, s
    assert "LEAF1001TESP03" in html
    assert "52489" in html and "sem" in html  # page sem resposta
    assert "gerado em 28/08/2026 08:01" in html
    assert "<script" not in html


def test_html_vazio_nao_quebra(tmp_path):
    q = QueryEngine(_seed(tmp_path))
    sm = q.summary(0, 1, "vazio")
    html = render_html(sm)
    assert "nenhuma page na janela" in html


def test_write_artifacts(tmp_path):
    sm = _summary(tmp_path, "ontem")
    html = render_html(sm)
    art = write_artifacts(tmp_path / "rel", sm, html, b"%PDF-fake", kind="daily")
    assert art.dir.name == "2026-08-28"
    assert art.html_path.read_text(encoding="utf-8") == html
    assert art.pdf_path.read_bytes() == b"%PDF-fake"
    data = json.loads(art.json_path.read_text(encoding="utf-8"))
    assert data["meta"]["kind"] == "daily" and data["summary"]["total"] == 1
    assert data["pages"][0]["page_id"] == 52488
    art2 = write_artifacts(tmp_path / "rel", sm, html, None, kind="daily")
    assert art2.pdf_path is None


def test_pdf_se_weasyprint_disponivel(tmp_path):
    pytest.importorskip("weasyprint")
    pdf = render_pdf(render_html(_summary(tmp_path)))
    if pdf is None:
        pytest.skip("weasyprint sem pango nesta máquina")
    assert pdf[:5] == b"%PDF-"

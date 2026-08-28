"""Corvo — renderização do relatório diário (Block Kit · HTML · PDF · JSON).

O resumo Slack vem de ``bot.summary_blocks`` (mesma função dos comandos). O
HTML é o artefato canônico; o PDF é o HTML via weasyprint — se a lib não
estiver disponível na box, o job segue e anexa o HTML.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.corvo.bot import summary_blocks
from app.corvo.datadog_metrics import fmt_duration
from app.corvo.datadog_query import BRT

TEMPLATES = Path(__file__).parent / "templates"
VERSION = "corvo-datadog 0.1"
MAX_TABLE_ROWS = 150  # acima disso a tabela do PDF corta (o JSON tem tudo)


@dataclass
class Artifacts:
    dir: Path
    html_path: Path
    pdf_path: Path | None
    json_path: Path


def build_blocks(summary: dict, kind: str = "ontem") -> tuple[list[dict], str]:
    return summary_blocks(summary, kind)


def _env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["dur"] = fmt_duration
    env.filters["pct"] = lambda n, total: f"{round(100 * n / total)}%" if total else "—"
    env.filters["hm"] = lambda iso: datetime.fromisoformat(iso).strftime("%H:%M") if iso else "—"
    return env


def render_html(
    summary: dict, *, generated_at: datetime | None = None, notes: list[str] | None = None
) -> str:
    env = _env()
    tpl = env.get_template("datadog_report.html")
    css = (TEMPLATES / "datadog_report.css").read_text(encoding="utf-8")
    gen = (generated_at or datetime.now(BRT)).astimezone(BRT)
    sm = summary
    max_dc = max([1, *sm["by_dc"].values()])
    max_hist = max([1, *(h["count"] for h in sm["histogram"])])
    max_team = max([1, *sm["by_team"].values()])
    max_urg = max([1, *sm["by_urgency"].values()])
    max_top30 = max([1, *(x["count"] for x in sm["top_30d"])])
    table_pages = sm["pages"][:MAX_TABLE_ROWS]
    table_truncated = max(0, len(sm["pages"]) - len(table_pages))
    return tpl.render(
        table_pages=table_pages,
        table_truncated=table_truncated,
        sm=sm,
        css=css,
        generated_at=gen.strftime("%d/%m/%Y %H:%M"),
        version=VERSION,
        notes=notes or [],
        max_dc=max_dc,
        max_hist=max_hist,
        max_team=max_team,
        max_urg=max_urg,
        max_top30=max_top30,
    )


def render_pdf(html: str) -> bytes | None:
    """PDF via weasyprint; None se a lib (ou pango) não estiver disponível."""
    try:
        from weasyprint import HTML
    except Exception:  # noqa: BLE001 — import falha sem pango/cairo; degrada para HTML
        return None
    try:
        return HTML(string=html, base_url=str(TEMPLATES)).write_pdf()
    except Exception:  # noqa: BLE001
        return None


def write_artifacts(
    report_dir: Path,
    summary: dict,
    html: str,
    pdf: bytes | None,
    *,
    kind: str = "daily",
    stamp: str | None = None,
) -> Artifacts:
    end = datetime.fromtimestamp(summary["window"]["end"], BRT)
    day = stamp or end.strftime("%Y-%m-%d")
    out = report_dir / day
    out.mkdir(parents=True, exist_ok=True)
    base = f"corvo-datadog-{kind}-{day}"
    html_path = out / f"{base}.html"
    html_path.write_text(html, encoding="utf-8")
    pdf_path = None
    if pdf:
        pdf_path = out / f"{base}.pdf"
        pdf_path.write_bytes(pdf)
    json_path = out / f"{base}.json"
    payload = {
        "meta": {
            "version": VERSION,
            "generated_at": datetime.now(BRT).isoformat(timespec="seconds"),
            "generated_ts": time.time(),
            "kind": kind,
            "provenance": "OBS · Slack #datadog-redes (history + eventos Socket Mode)",
            "ack_rule": "live > edited_ts > proxy(1ª resposta humana)",
        },
        "summary": {k: v for k, v in summary.items() if k != "pages"},
        "pages": summary["pages"],
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return Artifacts(out, html_path, pdf_path, json_path)

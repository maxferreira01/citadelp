#!/usr/bin/env python3
"""CITADEL · CORVO — relatório diário do #datadog-redes → DM do Bruno.

Lê o canal (Slack Web API, só leitura), atualiza o store SQLite, monta o resumo
(Block Kit), o HTML/PDF e o JSON, e opcionalmente posta na DM. Toda regra de
métrica vive em app/corvo (QueryEngine); este arquivo é só o entrypoint.

Uso:
    python collectors/corvo_datadog_report.py --dry-run                 # gera artefatos, não posta
    python collectors/corvo_datadog_report.py --dry-run --days 7        # backfill/relatório semanal
    python collectors/corvo_datadog_report.py --send                    # posta para CORVO_REPORT_TO
    python collectors/corvo_datadog_report.py --send --to U053RFRVBE1   # teste: só para mim
    python collectors/corvo_datadog_report.py --dump-raw --dry-run      # salva mensagens cruas p/ depurar parser

Variáveis (.env na raiz): SLACK_BOT_TOKEN, CORVO_DATADOG_CHANNEL_ID, CORVO_REPORT_TO,
CORVO_DATA_DIR, CORVO_REPORT_DIR. Sem token válido só funciona --offline (usa o store).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.corvo import slack_client as sc  # noqa: E402
from app.corvo.datadog_query import BRT, QueryEngine, anchor_08, daily_window  # noqa: E402
from app.corvo.datadog_report import build_blocks, render_html, render_pdf, write_artifacts  # noqa: E402
from app.corvo.datadog_scan import scan_channel  # noqa: E402
from app.corvo.datadog_store import Store  # noqa: E402
from app.corvo.settings import Settings  # noqa: E402


def log(msg: str) -> None:
    print(f"[{datetime.now(BRT):%H:%M:%S}] {msg}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", help="fim da janela (YYYY-MM-DD, 08:00 BRT). Default: hoje")
    ap.add_argument("--days", type=int, default=1, help="tamanho da janela em dias (default 1)")
    ap.add_argument("--send", action="store_true", help="posta na DM (CORVO_REPORT_TO ou --to)")
    ap.add_argument("--to", help="user id(s) Slack separados por vírgula (override)")
    ap.add_argument("--dry-run", action="store_true", help="não posta; grava artefatos e imprime os blocks")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--offline", action="store_true", help="não lê o Slack; usa só o store")
    ap.add_argument("--skip-replies", action="store_true", help="não busca threads (mais rápido)")
    ap.add_argument("--scan-days", type=int, default=None,
                    help="quantos dias reler do canal (default: janela + 1). Use 30 no 1º run")
    ap.add_argument("--dump-raw", action="store_true", help="salva mensagens cruas em relatorios/…/raw.json")
    args = ap.parse_args()
    if not args.send and not args.dry_run:
        args.dry_run = True

    settings = Settings.from_env()
    store = Store(settings.db_path)
    engine = QueryEngine(store)

    # sem --date: última janela FECHADA (08:00 BRT mais recente), nunca uma no futuro
    end_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=BRT) if args.date else anchor_08(datetime.now(BRT))
    start, end, label = daily_window(end_date, args.days)
    log(f"janela {label} · store {settings.db_path}")

    client = None
    if not args.offline:
        if not settings.token_ok():
            log("SLACK_BOT_TOKEN ausente/placeholder — rodando --offline (só o store)")
        else:
            client = sc.make_client(settings.slack_bot_token)
            scan_days = args.scan_days or (args.days + 1)
            oldest = end - scan_days * 86400
            t = time.time()
            res = scan_channel(client, store, settings.channel_id, oldest, latest=None,
                               fetch_replies=not args.skip_replies,
                               response_window_s=settings.response_window_s, keep_raw=args.dump_raw)
            log(f"scan: {res.pages} pages ({res.pages_new} novas) · {res.handovers} handovers · "
                f"{res.human_msgs} msgs humanas · {res.replies_fetched} threads · {time.time() - t:.0f}s")
            if res.unparsed_bot_msgs:
                log(f"ATENÇÃO: {len(res.unparsed_bot_msgs)} mensagens do bot não parseadas "
                    f"(ex.: {res.unparsed_bot_msgs[0]['text'][:80]!r})")
            if args.dump_raw:
                d = settings.report_dir / datetime.fromtimestamp(end, BRT).strftime("%Y-%m-%d")
                d.mkdir(parents=True, exist_ok=True)
                (d / "raw.json").write_text(json.dumps(res.raw, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
                log(f"raw salvo em {d / 'raw.json'} ({len(res.raw)} mensagens)")

    sm = engine.summary(start, end, label)
    kind = "daily" if args.days == 1 else f"{args.days}d"
    notes = []
    if client is None:
        notes.append("Relatório gerado a partir do store local, sem releitura do Slack (--offline).")
    html = render_html(sm, notes=notes)
    pdf = None if args.no_pdf else render_pdf(html)
    if not args.no_pdf and pdf is None:
        log("weasyprint indisponível — anexando HTML no lugar do PDF")
    art = write_artifacts(settings.report_dir, sm, html, pdf, kind=kind)
    blocks, text = build_blocks(sm, "ontem" if args.days == 1 else f"{args.days}d")
    log(f"{sm['total']} pages · resposta mediana {sm['response']['median']} s · "
        f"sem resposta {len(sm['unanswered'])} · artefatos em {art.dir}")

    if args.dry_run:
        print(json.dumps(blocks, ensure_ascii=False, indent=1))
        store.add_report(start, end, kind, str(art.html_path), str(art.pdf_path) if art.pdf_path else None,
                         str(art.json_path), None, None, time.time())
        return 0

    if client is None:
        log("não dá pra enviar sem token válido"); return 2
    targets = [x.strip() for x in (args.to or "").split(",") if x.strip()] or settings.report_to
    if not targets:
        log("defina CORVO_REPORT_TO ou --to"); return 2
    sent = []
    for uid in targets:
        try:
            ch = sc.open_dm(client, uid) if uid.startswith(("U", "W")) else uid
            ts = sc.post_blocks(client, ch, blocks, text)
            attach = art.pdf_path or art.html_path
            sc.upload_file(client, ch, attach, attach.name, thread_ts=ts,
                           initial_comment="Relatório completo em anexo.")
            sent.append(uid)
            log(f"enviado para {uid} ({ch})")
        except Exception as exc:  # noqa: BLE001
            log(f"ERRO enviando para {uid}: {exc}")
    store.add_report(start, end, kind, str(art.html_path), str(art.pdf_path) if art.pdf_path else None,
                     str(art.json_path), ",".join(sent) or None,
                     datetime.now(BRT).isoformat(timespec="seconds") if sent else None, time.time())
    return 0 if sent else 1


if __name__ == "__main__":
    raise SystemExit(main())

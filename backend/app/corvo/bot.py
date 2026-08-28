"""Corvo — roteador de comandos da DM (puro; sem Slack, sem LLM).

O Bruno fala com o app por palavras-chave fixas. ``route()`` normaliza o texto
(minúsculas, sem acento, sem menção) e devolve um ``Command``; ``handle()``
monta a resposta (blocks + texto + arquivo opcional) usando só o QueryEngine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from app.corvo.datadog import strip_accents
from app.corvo.datadog_metrics import fmt_duration
from app.corvo.datadog_query import PERIOD_KINDS, QueryEngine, period

PERIOD_ALIASES = {
    "hoje": "hoje",
    "ontem": "ontem",
    "7d": "7d",
    "7 dias": "7d",
    "semana": "7d",
    "30d": "30d",
    "30 dias": "30d",
    "mes": "mes",
    "mes atual": "mes",
    "este mes": "mes",
    "mes anterior": "mes_anterior",
    "mes passado": "mes_anterior",
}

# (nome do comando, regex sobre o texto normalizado)
COMMANDS: list[tuple[str, re.Pattern]] = [
    ("ajuda", re.compile(r"^(ajuda|help|\?|comandos)\b")),
    (
        "reenviar",
        re.compile(r"^(reenviar|reenvia|manda|mandar|envia|enviar)\b.*\b(pdf|relatorio)|^pdf$"),
    ),
    ("alerta", re.compile(r"^(alerta|page|pagina|inc|chamado)\b\s*#?\s*([a-z0-9_-]+)")),
    ("plantao", re.compile(r"\b(plantao|plantonista|oncall|on-call|quem esta de plantao|quem)\b")),
    ("mes", re.compile(r"\b(quantos|chamados|pages|alertas)\b.*\b(mes)\b|^mes$|^mes\b")),
    ("semresposta", re.compile(r"\b(sem resposta|nao respondid|ignorad|pendente)")),
    ("tempo", re.compile(r"\b(tempo|mtta|mttr|resposta|demora)\b")),
    ("topdc", re.compile(r"\b(top\s*dc|datacenters?|dcs?|sites?)\b")),
    ("recorrentes", re.compile(r"\b(recorren|repetid|reincid)")),
    (
        "resumo",
        re.compile(r"^(resumo|relatorio|report)?\s*(hoje|ontem|\d{1,3}\s*(d|dias?)|semana)\b"),
    ),
    # frases naturais: "quero relatório", "me dá um relatório do dia", "resumo" → hoje
    ("resumo", re.compile(r"\b(relatorio|report|resumo|status)\b")),
]


@dataclass
class Command:
    name: str
    arg: str | None = None
    period: str | None = None
    raw: str = ""


@dataclass
class Reply:
    blocks: list[dict]
    text: str
    file: Path | None = None
    file_title: str | None = None


class BotContext(Protocol):
    engine: QueryEngine

    def render_pdf_for(self, kind: str, now: datetime) -> Path | None: ...

    def last_pdf(self) -> Path | None: ...


def normalize(text: str) -> str:
    t = re.sub(r"<@[UW][A-Z0-9]+(\|[^>]*)?>", " ", text or "")
    t = strip_accents(t).lower()
    t = re.sub(r"[^\w\s#?-]", " ", t)
    return " ".join(t.split())


def _extract_period(t: str) -> tuple[str | None, str]:
    """Acha um período no texto; devolve (kind, texto sem o período)."""
    m = re.search(r"(?<![\w-])(\d{1,3})\s*(?:d|dias?)(?![\w-])", t)
    if m:
        n = int(m.group(1))
        kind = {1: "hoje", 7: "7d", 30: "30d"}.get(n, f"{n}d") if n != 1 else "ontem"
        return kind, (t[: m.start()] + " " + t[m.end() :]).strip()
    for alias in sorted(PERIOD_ALIASES, key=len, reverse=True):
        m = re.search(rf"(?<![\w-]){re.escape(alias)}(?![\w-])", t)
        if m:
            return PERIOD_ALIASES[alias], (t[: m.start()] + " " + t[m.end() :]).strip()
    return None, t


def route(text: str) -> Command:
    t = normalize(text)
    if not t:
        return Command("ajuda", raw=text)
    for name, rx in COMMANDS:
        m = rx.search(t)
        if not m:
            continue
        if name == "alerta":
            return Command("alerta", arg=m.group(2), raw=text)
        if name == "resumo":
            kind, _ = _extract_period(t)
            return Command("resumo", period=kind or "hoje", raw=text)
        kind, _ = _extract_period(t)
        return Command(name, period=kind, raw=text)
    kind, rest = _extract_period(t)
    if kind and not rest:
        return Command("resumo", period=kind, raw=text)
    return Command("ajuda", arg=t, raw=text)


def is_allowed(user_id: str, allowed: set[str] | list[str]) -> bool:
    return not allowed or user_id in set(allowed)


# ------------------------------------------------------------------ blocks
def _section(md: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": md[:2900]}}


def _header(txt: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": txt[:150], "emoji": True}}


def _context(md: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": md[:2900]}]}


def _buttons(labels: list[tuple[str, str]]) -> dict:
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": lbl, "emoji": True},
                "action_id": f"corvo_cmd_{i}",
                "value": val,
            }
            for i, (lbl, val) in enumerate(labels)
        ],
    }


def _user(uid: str | None, name: str | None) -> str:
    if not uid:
        return "—"
    return f"<@{uid}>" if not name or name == uid else f"{name} (<@{uid}>)"


def _stat_line(label: str, s: dict) -> str:
    if not s or not s.get("n"):
        return f"*{label}:* sem dados"
    return (
        f"*{label}:* mediana {fmt_duration(s['median'])} · p90 {fmt_duration(s['p90'])} · "
        f"máx {fmt_duration(s['max'])} (n={s['n']})"
    )


HELP = (
    "*Comandos do Corvo* (é só escrever aqui na DM):\n"
    "• `hoje` · `ontem` · `7d` · `30d` — resumo do período (+ PDF)\n"
    "• `plantão` — quem está de plantão (Interna/Externa)\n"
    "• `mês` — quantos chamados no mês, por time e por DC\n"
    "• `tempo médio [7d|30d|mês]` — tempo de resposta e de ack\n"
    "• `top dc [período]` — datacenters que mais aparecem\n"
    "• `recorrentes [período]` — alertas repetidos\n"
    "• `sem resposta [período]` — pages sem ninguém\n"
    "• `alerta 52488` / `alerta INC13450` — detalhe de uma page\n"
    "• `reenviar pdf` — último relatório em PDF\n"
    "_Período padrão: 30d nas consultas; o relatório diário cobre 08:00→08:00._"
)


def handle(cmd: Command, ctx: BotContext, now: datetime) -> Reply:
    q = ctx.engine
    name = cmd.name
    if name == "ajuda":
        blocks = [
            _section(HELP),
            _buttons(
                [
                    ("Hoje", "hoje"),
                    ("Ontem", "ontem"),
                    ("Plantão", "plantao"),
                    ("Mês", "mes"),
                    ("Tempo médio", "tempo medio"),
                ]
            ),
        ]
        text = "Comandos: hoje, ontem, 7d, 30d, plantão, mês, tempo médio, top dc, recorrentes, sem resposta, alerta <id>, reenviar pdf"  # noqa: E501
        if cmd.arg:
            blocks.insert(0, _context(f"Não entendi `{cmd.arg[:60]}`. Veja os comandos:"))
        return Reply(blocks, text)

    if name == "reenviar":
        f = ctx.last_pdf()
        if not f:
            return Reply(
                [_section("Ainda não há PDF gerado. Peça `ontem` ou `7d` que eu gero um.")],
                "Sem PDF ainda",
            )
        return Reply(
            [_section(f"Último relatório: `{f.name}`")],
            f"Reenviando {f.name}",
            file=f,
            file_title=f.name,
        )

    if name == "resumo":
        kind = cmd.period or "hoje"
        s, e, label = period(kind, now)
        sm = q.summary(s, e, label)
        blocks, text = summary_blocks(sm, kind)
        pdf = ctx.render_pdf_for(kind, now) if sm["total"] else None
        return Reply(blocks, text, file=pdf, file_title=pdf.name if pdf else None)

    if name == "plantao":
        oc = q.oncall()
        s, e, _ = period("hoje", now)
        sm = q.summary(s, e)
        lines = []
        for sched in ("Interna", "Externa"):
            r = oc.get(sched)
            if r and r.get("user"):
                lines.append(
                    f"*Plantão Redes {sched}:* {_user(r['user'], r.get('name'))} · desde {r['since_hm']}"  # noqa: E501
                )
            elif r and r.get("last"):
                lines.append(
                    f"*Plantão Redes {sched}:* _sem plantão ativo (Empty desde {r['since_hm']})_ · "
                    f"último: {_user(r['last']['user'], r['last'].get('name'))}"
                )
            else:
                lines.append(f"*Plantão Redes {sched}:* _sem handover registrado_")
        top = ", ".join(f"{r['name']} ({r['pages']})" for r in sm["responders"][:5]) or "—"
        lines.append(f"*Responders desde 08:00:* {top}")
        if not any(oc.get(k) for k in ("Interna", "Externa")):
            lines.append("_Ainda não vi nenhum Handover Summary no canal — rode um scan de 7d._")
        return Reply([_header("Plantão"), _section("\n".join(lines))], "\n".join(lines))

    if name == "mes":
        m = q.count_month(now)
        team = " · ".join(f"{k}: {v}" for k, v in m["by_team"].items()) or "—"
        dc = " · ".join(f"{k}: {v}" for k, v in list(m["by_dc"].items())[:8]) or "—"
        kind = " · ".join(f"{k}: {v}" for k, v in m["by_kind"].items()) or "—"
        delta = m["total"] - m["prev_total"]
        sign = "+" if delta >= 0 else ""
        md = (
            f"*Chamados no {m['label']}:* {m['total']}  ({sign}{delta} vs {m['prev_label']}: {m['prev_total']})\n"  # noqa: E501
            f"*Por tipo:* {kind}\n*Por time:* {team}\n*Por DC:* {dc}"
        )
        return Reply([_header("Chamados do mês"), _section(md)], md)

    if name == "tempo":
        kind = cmd.period or "30d"
        s, e, label = period(kind, now)
        rs = q.response_stats(s, e)
        src = rs["ack_sources"]
        md = (
            f"*Período:* {label} · {rs['total']} pages\n"
            f"{_stat_line('Resposta humana no Slack', rs['response'])}\n"
            f"{_stat_line('Ack no Datadog (exato)', rs['ack_exact'])}\n"
            f"{_stat_line('Ack no Datadog (todos, c/ proxy)', rs['ack_all'])}\n"
            f"{_stat_line('Primeiro toque', rs['first_touch'])}\n"
            f"{_stat_line('Resolução', rs['resolve'])}\n"
            f"*Sem resposta:* {rs['unanswered']} · *ack silencioso:* {rs['silent_ack']} · "
            f"_fontes do ack: {', '.join(f'{k} {v}' for k, v in src.items()) or '—'}_"
        )
        return Reply([_header("Tempo de resposta"), _section(md)], md)

    if name == "topdc":
        kind = cmd.period or "30d"
        s, e, label = period(kind, now)
        top = q.top_dcs(s, e)
        lines = [f"{i + 1}. *{r['dc']}* — {r['count']} ({r['pct']}%)" for i, r in enumerate(top)]
        md = f"*Período:* {label}\n" + ("\n".join(lines) or "_sem pages_")
        return Reply([_header("Top datacenters"), _section(md)], md)

    if name == "recorrentes":
        kind = cmd.period or "30d"
        s, e, label = period(kind, now)
        rec = q.recurrent(s, e)
        lines = [f"• `{r['key'].replace('|', ' · ')}` ×{r['count']}" for r in rec["alert"]]
        incs = [f"• INC `{r['inc']}` ×{r['count']}" for r in rec["inc"]]
        md = f"*Período:* {label}\n" + ("\n".join(lines) or "_nenhum alerta repetido_")
        if incs:
            md += "\n*INCs repetidos:*\n" + "\n".join(incs)
        return Reply([_header("Alertas recorrentes"), _section(md)], md)

    if name == "semresposta":
        kind = cmd.period or "30d"
        s, e, label = period(kind, now)
        un = q.unanswered(s, e)
        lines = [
            f"• {p['hora']} <{p['page_url']}|#{p['page_id']}> {p['servidor'] or p['title']} "
            f"— {p['evento'] or ''} ({p['dc'] or '?'}, {p['status'] or '?'})"
            for p in un[:30]
        ]
        md = f"*Período:* {label} · {len(un)} sem resposta\n" + ("\n".join(lines) or "_nenhuma_ 🎉")
        return Reply([_header("Sem resposta"), _section(md)], md)

    if name == "alerta":
        card = q.page_card(cmd.arg or "")
        if not card:
            return Reply(
                [_section(f"Não achei page/INC `{cmd.arg}` no que já coletei.")],
                f"Page {cmd.arg} não encontrada",
            )
        md = page_card_md(card)
        return Reply([_header(f"Page #{card['page_id']}"), _section(md)], md)

    return handle(Command("ajuda", raw=cmd.raw), ctx, now)


def page_card_md(c: dict) -> str:
    tl = (
        " → ".join(
            f"{t['status']} {datetime.fromisoformat(t['iso']).strftime('%H:%M')}"
            f"{' (' + t['source'] + ')' if t['source'] != 'live' else ''}"
            for t in c["timeline"]
        )
        or "—"
    )
    who = (
        ", ".join(
            f"{e['name']} ({e['kind']}, {fmt_duration(e['ts'] - c['t0'])})" for e in c["events"][:6]
        )
        or "—"
    )
    lines = [
        f"<{c['page_url']}|*#{c['page_id']}* {c['title']}>",
        f"*Disparo:* {c['hora']} · *Status:* {c['status'] or '?'} · *Urgência:* {c['urgency'] or '?'} · "  # noqa: E501
        f"*Time:* {c['team'] or '?'} · *Tipo:* {c['kind']}",
        f"*Servidor:* `{c['servidor'] or '—'}` · *DC:* {c['dc'] or '?'} · *Evento:* {c['evento'] or '—'} · "  # noqa: E501
        f"*INC:* {c['inc'] or '—'}",
        f"*Responder (Datadog):* {_user(c['responder'], c.get('responder_name'))}",
        f"*Ack:* {fmt_duration(c['ack_s'])} ({c['ack_source'] or 'desconhecido'}) · "
        f"*Resposta no Slack:* {fmt_duration(c['response_s'])} · *Resolução:* {fmt_duration(c['resolve_s'])}",  # noqa: E501
        f"*Timeline:* {tl}",
        f"*Quem falou:* {who}",
        f"*Recorrência:* ×{c['d7']} em 7d · ×{c['d30']} em 30d · mesmo INC: {len(c['same_inc'])} page(s)",  # noqa: E501
    ]
    if c.get("requested_by"):
        lines.append(
            f"*Acionamento por:* {c['requested_by']} — _{(c.get('justificativa') or '')[:300]}_"
        )
    if c.get("descricao"):
        lines.append(f"_{c['descricao'][:300]}_")
    return "\n".join(lines)


STATUS_ICON = {"Resolved": "✅", "Acknowledged": "⚠️", "Triggered": "🔴"}
MAX_PAGE_LINES = 20


def _mention(uid: str | None, name: str | None = None) -> str:
    if uid:
        return f"<@{uid}>"
    return name or "—"


def _page_line(p: dict) -> str:
    hora = p["hora"][-5:]
    icon = STATUS_ICON.get(p.get("status") or "", "•")
    if p["kind"] == "manual":
        label = f"acionamento por {p.get('requested_by') or '?'} · {p.get('inc') or ''}".strip(" ·")
    else:
        label = (
            f"{p.get('servidor') or p.get('title') or '?'} · {(p.get('evento') or '')[:40]}".strip(
                " ·"
            )
        )
    dc = p.get("dc") or "sem DC"
    if p.get("unanswered"):
        who = "🔴 *sem resposta*"
    else:
        parts = []
        if p.get("response_user_name"):
            parts.append(f"{p['response_user_name']} respondeu em {fmt_duration(p['response_s'])}")
        if p.get("responder"):
            ack = f"ack {p.get('responder_name') or p['responder']}"
            if p.get("ack_s") is not None and p.get("ack_source") in ("live", "edited_ts"):
                ack += f" em {fmt_duration(p['ack_s'])}"
            if p.get("silent_ack"):
                ack += " (sem msg no Slack)"
            parts.append(ack)
        if p.get("resolve_s") is not None:
            parts.append(f"resolvido {fmt_duration(p['resolve_s'])}")
        who = " · ".join(parts) or "—"
    return f"{icon} `{hora}` <{p['page_url']}|#{p['page_id']}> {label} · _{dc}_ — {who}"


def _chunk_sections(lines: list[str], limit: int = 2800) -> list[dict]:
    out, buf = [], ""
    for ln in lines:
        if buf and len(buf) + len(ln) + 1 > limit:
            out.append(_section(buf))
            buf = ""
        buf = f"{buf}\n{ln}" if buf else ln
    if buf:
        out.append(_section(buf))
    return out


def summary_blocks(sm: dict, kind: str = "ontem") -> tuple[list[dict], str]:
    """Resumo Block Kit usado pelo relatório diário e pelos comandos hoje/ontem/7d/30d."""
    w = sm["window"]
    total = sm["total"]
    bk, st = sm["by_kind"], sm["by_status"]
    n_un = len(sm["unanswered"])
    r, a = sm["response"], sm["ack_all"]
    oc = sm["oncall"]

    title = f"Corvo · Datadog On-Call — {w['label']}"
    un_txt = f"🔴 {n_un} ({sm['unanswered_pct']}%)" if n_un else "✅ 0"
    resp_txt = (
        f"mediana {fmt_duration(r['median'])} · p90 {fmt_duration(r['p90'])} (n={r['n']})"
        if r["n"]
        else "ninguém respondeu no Slack"
    )
    ack_txt = (
        f"mediana {fmt_duration(a['median'])} · máx {fmt_duration(a['max'])} (n={a['n']})"
        if a["n"]
        else "sem ack registrado"
    )
    if sm["silent_ack"]:
        ack_txt += f" · {len(sm['silent_ack'])} sem msg no Slack"
    status_txt = (
        " · ".join(f"{STATUS_ICON.get(k, '•')} {v} {k.lower()}" for k, v in st.items()) or "—"
    )
    plant = []
    for k in ("Interna", "Externa"):
        v = oc.get(k)
        if v and v.get("user"):
            plant.append(f"{k} {_mention(v['user'])}")
        elif v and v.get("last"):
            plant.append(f"{k} — (último {_mention(v['last']['user'])})")
        else:
            plant.append(f"{k} —")
    fields = [
        f"*Pages*\n{total} · {bk.get('auto', 0)} auto · {bk.get('manual', 0)} acionamento(s)",
        f"*Sem resposta*\n{un_txt}",
        f"*Resposta humana no Slack*\n{resp_txt}",
        f"*Ack no Datadog*\n{ack_txt}",
        f"*Status agora*\n{status_txt}",
        f"*Plantão*\n{' · '.join(plant)}",
    ]
    blocks: list[dict] = [
        _header(title),
        {"type": "section", "fields": [{"type": "mrkdwn", "text": f[:2000]} for f in fields]},
        {"type": "divider"},
    ]

    pages = sm["pages"]
    if pages:
        lines = [_page_line(p) for p in pages[:MAX_PAGE_LINES]]
        if len(pages) > MAX_PAGE_LINES:
            lines.append(f"_… +{len(pages) - MAX_PAGE_LINES} pages no PDF_")
        blocks.append(_section(f"*Pages do período ({total})*"))
        blocks.extend(_chunk_sections(lines))
    else:
        blocks.append(_section("*Pages do período:* nenhuma 🎉"))

    hl = []
    dcs = [(("sem DC" if k == "?" else k), v) for k, v in list(sm["by_dc"].items())[:5]]
    if dcs:
        hl.append("*DCs:* " + " · ".join(f"{k} {v}" for k, v in dcs))
    rec = sm["recurrent_day"][:3]
    if rec:
        hl.append(
            "*Recorrentes:* "
            + " · ".join(
                f"{x['key'].split('|')[0].lower()} {x['key'].split('|')[1]} ×{x['count']} "
                f"({x['d7']} em 7d, {x['d30']} em 30d)"
                for x in rec
            )
        )
    top = sm["top_30d"][:3]
    if top:
        hl.append(
            "*Mais frequentes em 30d:* "
            + " · ".join(
                f"{x['key'].split('|')[0].lower()} {x['key'].split('|')[1][:30]} ×{x['count']}"
                for x in top
            )
        )
    resp = ", ".join(f"{x['name']} {x['pages']}" for x in sm["responders"][:5])
    if resp:
        hl.append(f"*Responders (Datadog):* {resp}")
    if hl:
        blocks.append({"type": "divider"})
        blocks.append(_section("\n".join(hl)))

    blocks.append(
        _buttons(
            [
                ("7d", "7d"),
                ("30d", "30d"),
                ("Plantão", "plantao"),
                ("Tempo médio", "tempo medio"),
                ("Reenviar PDF", "reenviar pdf"),
            ]
        )
    )
    blocks.append(
        _context(
            "fonte: #datadog-redes (Slack) · ack exato só com o bot ouvindo o canal; antes disso o ack é "  # noqa: E501
            "aproximado pela 1ª resposta humana · PDF completo na thread"
        )
    )
    text = f"{title} — {total} pages, {n_un} sem resposta, resposta mediana {fmt_duration(r['median'])}"  # noqa: E501
    return blocks, text


__all__ = [
    "Command",
    "Reply",
    "BotContext",
    "route",
    "handle",
    "is_allowed",
    "normalize",
    "summary_blocks",
    "page_card_md",
    "PERIOD_KINDS",
]

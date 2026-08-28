"""Corvo — parser puro das mensagens do Datadog On-Call no #datadog-redes.

Regras validadas na leitura do canal em 28/08/2026 (page #52488, #52486,
#52481 manual, #52477 Team Float IP, #52425 ainda Acknowledged):

- Uma mensagem por page; o Datadog EDITA a mesma mensagem quando a page muda
  de estado (Triggered → Acknowledged → Resolved). O histórico só tem o estado
  atual — o tempo exato de ack vem do evento ``message_changed`` (bot_app).
- Título: ``Page #NNNN: <host> <evento> on cherwellincidentid:<INC>``.
  Variante manual: ``Page #NNNN: Acionamento para InfraOPS Redes (Incidente: INCxxxx)``.
- Corpo em bullets ``- Servidor / - Evento / - Descrição / - INC / - Status /
  - Origem / - Team``. A variante "Team Float IP" traz ``Status: *error*``
  antes dos bullets e pode não ter Responder.
- Handover diário: ``Handover Summary`` + uma linha por schedule
  (``Plantao Redes Interna/Externa``) terminando no usuário que entra.
"""

from __future__ import annotations

import re
import unicodedata
import urllib.parse
from datetime import UTC, datetime

DATADOG_BOT_USER = "U07Q4UQU0GM"

# Família de datacenters conhecida (mesma do runbook ACI). Normalizada: 2 dígitos.
KNOWN_DCS = frozenset(
    {"TESP02", "TESP03", "TESP04", "TESP05", "TESP06", "TESP07", "TECE01", "TBSP02", "TBCE01"}
)

_PAGE_ID_RE = re.compile(r"Page\s*#(?P<id>\d+)\s*:\s*(?P<title>[^\n>]*)")
_PAGE_URL_RE = re.compile(r"https?://app\.datadoghq\.com/on-call/pages/(\d+)")
_TITLE_INC_RE = re.compile(r"\s*on\s+cherwellincidentid:\s*(?P<inc>[A-Za-z0-9_-]+)\s*$", re.I)
_STATUS_RE = re.compile(r"\*Status:\*\s*(?::[\w+-]+:\s*)?(Triggered|Acknowledged|Resolved)\b", re.I)
_STATUS_PLAIN_RE = re.compile(
    r"(?m)^\s*Status:\s*\n?\s*(?::[\w+-]+:\s*)?(Triggered|Acknowledged|Resolved)\b", re.I
)
_URGENCY_RE = re.compile(r"\*?Urgency:\*?\s*\n?\s*(High|Medium|Low)\b", re.I)
_TEAM_RE = re.compile(r"\*Team:\*\s*\n?\s*([^\n]+)")
_TEAM_PLAIN_RE = re.compile(r"(?m)^\s*Team:\s*\n?\s*([^\n]+)")
_RESPONDER_RE = re.compile(r"\*?Responder:\*?\s*\n?\s*<@([UW][A-Z0-9]+)(?:\|[^>]*)?>")
_BULLET_RES = {
    "servidor": re.compile(r"(?m)^\s*[-•]\s*Servidor:\s*(.+?)\s*$"),
    "evento": re.compile(r"(?m)^\s*[-•]\s*Evento:\s*(.+?)\s*$"),
    "descricao": re.compile(r"(?m)^\s*[-•]\s*Descri[cç][aã]o:\s*(.+?)\s*$"),
    "inc": re.compile(r"(?m)^\s*[-•]\s*INC:\s*(\S+)"),
    "origem": re.compile(r"(?m)^\s*[-•]\s*Origem:\s*(\S+)"),
    "team_tag": re.compile(r"(?m)^\s*[-•]\s*Team:\s*(\S+)"),
}
_MONITOR_RE = re.compile(r"app\.datadoghq\.com/monitors/(\d+)\?group=([^&|>\s]+)")
_LAST_TRIGGERED_RE = re.compile(
    r"last triggered at\s+([A-Za-z]{3} [A-Za-z]{3} \d{1,2} \d{4} \d{2}:\d{2}:\d{2}) UTC"
)
_MANUAL_INC_RE = re.compile(r"Incidente:\s*\(?\s*([A-Za-z]{2,6}\d{3,}|\d{5,})\b")
_JUSTIFICATIVA_RE = re.compile(r"Justificativa:\s*(.+?)(?=\n\s*\(Acionamento solicitado|\Z)", re.S)
_REQUESTED_BY_RE = re.compile(r"Acionamento solicitado por:\s*([^)\n]+)")

_DC_SUFFIX_RE = re.compile(r"(T[A-Z]{3}\d{1,2})(?=$|[-_.])", re.I)
_DC_PREFIX_RE = re.compile(r"^(T[A-Z]{3}\d{1,2})(?=[A-Z_-])", re.I)
_DC_ANY_RE = re.compile(r"(T[A-Z]{3}\d{1,2})", re.I)

_HANDOVER_LINE_RE = re.compile(r"Plantao\s+Redes\s+(Interna|Externa)[^\n]*", re.I)
_MENTION_RE = re.compile(r"<@([UW][A-Z0-9]+)(?:\|([^>]*))?>")


# --------------------------------------------------------------------------- texto
def _rich_text(el: dict) -> str:
    t = el.get("type")
    if t == "text":
        return el.get("text", "")
    if t == "user":
        return f"<@{el.get('user_id', '')}>"
    if t == "link":
        url, txt = el.get("url", ""), el.get("text")
        return f"<{url}|{txt}>" if txt else f"<{url}>"
    if t == "emoji":
        return f":{el.get('name', '')}:"
    if t == "channel":
        return f"<#{el.get('channel_id', '')}>"
    return "".join(_rich_text(x) for x in el.get("elements", []))


def _blocks_text(blocks: list[dict]) -> list[str]:
    out: list[str] = []
    for b in blocks or []:
        t = b.get("type")
        if t in ("section", "header"):
            if isinstance(b.get("text"), dict):
                out.append(b["text"].get("text", ""))
            for f in b.get("fields") or []:
                out.append(f.get("text", ""))
        elif t == "context":
            for e in b.get("elements") or []:
                if isinstance(e, dict) and e.get("text"):
                    out.append(e["text"])
        elif t == "rich_text":
            for e in b.get("elements") or []:
                et = e.get("type")
                if et == "rich_text_list":
                    for item in e.get("elements", []):
                        out.append("- " + _rich_text(item))
                else:
                    out.append(_rich_text(e))
    return [x for x in out if x]


def attachment_text(msg: dict) -> str:
    """Achata text + attachments (title/text/fields/blocks) + blocks numa string
    com quebras de linha reais, na ordem em que o Slack renderiza."""
    parts: list[str] = []
    if msg.get("text"):
        parts.append(msg["text"])
    parts.extend(_blocks_text(msg.get("blocks") or []))
    for att in msg.get("attachments") or []:
        if att.get("pretext"):
            parts.append(att["pretext"])
        if att.get("title"):
            parts.append(att["title"])
        if att.get("title_link"):
            parts.append(att["title_link"])
        if att.get("text"):
            parts.append(att["text"])
        for f in att.get("fields") or []:
            parts.append(f"*{f.get('title', '')}*\n{f.get('value', '')}")
        parts.extend(_blocks_text(att.get("blocks") or []))
        if att.get("footer"):
            parts.append(att["footer"])
        # fallback por último: duplica o conteúdo, só serve se o resto vier vazio
        if att.get("fallback") and not (att.get("title") or att.get("text") or att.get("blocks")):
            parts.append(att["fallback"])
    return "\n".join(parts)


def is_datadog(msg: dict) -> bool:
    return msg.get("user") == DATADOG_BOT_USER or bool(msg.get("bot_id"))


def is_handover(blob: str) -> bool:
    return "Handover Summary" in blob


# --------------------------------------------------------------------------- DC
def normalize_dc(dc: str | None) -> str | None:
    if not dc:
        return None
    m = re.fullmatch(r"(T[A-Z]{3})(\d{1,2})", dc.strip().upper())
    if not m:
        return None
    return f"{m.group(1)}{int(m.group(2)):02d}"


def extract_dc(host: str | None) -> str | None:
    """DC a partir do hostname: sufixo (LEAF1001TESP03, FW01TECE01,
    monitoring-redes-1-tece01), prefixo (tesp3cmk1p00004-floating) ou qualquer
    token que normalize para um DC conhecido. Nunca inventa: None se não achar."""
    if not host:
        return None
    h = host.strip()
    for rx in (_DC_SUFFIX_RE, _DC_PREFIX_RE):
        m = rx.search(h)
        if m:
            return normalize_dc(m.group(1))
    for m in _DC_ANY_RE.finditer(h):
        n = normalize_dc(m.group(1))
        if n in KNOWN_DCS:
            return n
    return None


def _dc_in_text(text: str | None) -> str | None:
    if not text:
        return None
    for m in _DC_ANY_RE.finditer(text):
        n = normalize_dc(m.group(1))
        if n in KNOWN_DCS:
            return n
    return None


# --------------------------------------------------------------------------- page
def _first(rx: re.Pattern, blob: str, group: int = 1) -> str | None:
    m = rx.search(blob)
    return m.group(group).strip() if m else None


def parse_datadog_page(blob: str) -> dict | None:
    """Extrai uma page do texto achatado. None se não houver ``Page #``."""
    m = _PAGE_ID_RE.search(blob)
    if not m:
        return None
    page_id = int(m.group("id"))
    title = m.group("title").strip().rstrip("|").strip()
    inc_title = None
    mi = _TITLE_INC_RE.search(title)
    if mi:
        inc_title = mi.group("inc")
        title = title[: mi.start()].strip()

    page_url_m = _PAGE_URL_RE.search(blob)
    page_url = (
        page_url_m.group(0) if page_url_m else f"https://app.datadoghq.com/on-call/pages/{page_id}"
    )

    status = _first(_STATUS_RE, blob) or _first(_STATUS_PLAIN_RE, blob)
    status = status.capitalize() if status else None
    urgency = _first(_URGENCY_RE, blob)
    urgency = urgency.capitalize() if urgency else None
    team = _first(_TEAM_RE, blob) or _first(_TEAM_PLAIN_RE, blob)
    responder = _first(_RESPONDER_RE, blob)

    fields = {k: _first(rx, blob) for k, rx in _BULLET_RES.items()}
    requested_by = _first(_REQUESTED_BY_RE, blob)
    justificativa = _first(_JUSTIFICATIVA_RE, blob)
    manual = bool(requested_by) or title.lower().startswith("acionamento")
    inc = fields["inc"] or inc_title
    if manual and not inc:
        inc = _first(_MANUAL_INC_RE, blob)

    mon = _MONITOR_RE.search(blob)
    monitor_id = mon.group(1) if mon else None
    monitor_group = urllib.parse.unquote(mon.group(2)) if mon else None

    last_triggered_at = None
    lt = _LAST_TRIGGERED_RE.search(blob)
    if lt:
        try:
            last_triggered_at = (
                datetime.strptime(lt.group(1), "%a %b %d %Y %H:%M:%S")
                .replace(tzinfo=UTC)
                .isoformat()
            )
        except ValueError:
            last_triggered_at = None

    servidor = fields["servidor"]
    dc = extract_dc(servidor)
    if dc is None:
        dc = _dc_in_text(title) or _dc_in_text(justificativa) or _dc_in_text(fields["descricao"])

    return {
        "page_id": page_id,
        "page_url": page_url,
        "title": title,
        "kind": "manual" if manual else "auto",
        "status": status,
        "urgency": urgency,
        "team": team,
        "responder": responder,
        "servidor": servidor,
        "evento": fields["evento"],
        "descricao": fields["descricao"],
        "inc": inc,
        "origem": fields["origem"],
        "team_tag": fields["team_tag"],
        "requested_by": requested_by,
        "justificativa": justificativa,
        "last_triggered_at": last_triggered_at,
        "monitor_id": monitor_id,
        "monitor_group": monitor_group,
        "dc": dc,
    }


# --------------------------------------------------------------------------- handover
def parse_handover(blob: str) -> dict | None:
    """``{"schedules": {"Interna": "U…"|None, "Externa": ...}, "names": {...}}``.
    O usuário que ENTRA é a última menção da linha; ``(Empty)`` no fim = ninguém."""
    if not is_handover(blob):
        return None
    schedules: dict[str, str | None] = {}
    names: dict[str, str] = {}
    for m in _HANDOVER_LINE_RE.finditer(blob):
        key = m.group(1).capitalize()
        line = m.group(0)
        mentions = _MENTION_RE.findall(line)
        tail = line.rsplit(":arrow_right:", 1)[-1] if ":arrow_right:" in line else line
        if "(Empty)" in tail and not _MENTION_RE.search(tail):
            schedules[key] = None
            continue
        if mentions:
            uid, name = mentions[-1]
            schedules[key] = uid
            if name:
                names[uid] = name
        else:
            schedules[key] = None
    if not schedules:
        return None
    return {"schedules": schedules, "names": names}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

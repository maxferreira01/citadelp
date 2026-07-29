#!/usr/bin/env python3
"""Gera/atualiza o MD-fonte do relatório de consumo dos firewalls.

Um bloco por site Checkmk. Rode uma vez por site coletado; o bloco do site é
substituído se já existir (idempotente). O MD final é insumo para outra sessão
gerar o relatório executivo.

Uso: python scripts/relatorio_md.py <site_id> <consumo.json> <banda.csv> <dias> <md_out>
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))

CABECALHO = """\
# Relatório de Consumo — Firewalls (CPU · Memória · Sessões · Banda)

> **Documento-fonte de coleta.** Cada seção `## Site:` abaixo é gerada
> automaticamente por `scripts/relatorio_md.py` a partir das coletas nos sites
> Checkmk. Este arquivo alimenta a geração do relatório executivo final
> (ver "Instruções para o agente gerador" ao fim).

## Metodologia

- **Fonte instantânea (CPU/Mem/Sessões):** REST API Checkmk
  (`GET /domain-types/service/collections/all`, coluna `perf_data`), automation
  user dedicado. Valor = última coleta do agente no momento da execução.
- **Fonte histórica (Banda):** Livestatus TLS (porta 6557), colunas
  `rrddata:in/out` (average e max), RRA de 1 hora. Valores dos RRDs em bytes/s,
  convertidos para **Mbps** (×8/1e6).
- **Clusters HA:** no padrão deste ambiente, cada host-objeto de um par carrega
  serviços dos DOIS membros com sufixo (ex.: `CPU utilization FW02TBCE01`).
  O coletor separa por membro e deduplica — a tabela traz ativos E passivos.
  Passivos são identificáveis por CPU ~0% e sessões ~0.
- **Speed / PICO%:** velocidade da interface vem da perfdata (`in=...;;;0;SPEED`);
  `PICO%` = maior pico (in ou out) ÷ velocidade. Interfaces sem speed → `-`.
- Scripts: `scripts/fw_consumo.py` (instantâneo) e `scripts/fw_banda.py`
  (histórico) no repo CITADEL.

## Dicionário de dados

| Coluna | Significado |
|---|---|
| CPU% | Utilização de CPU no momento da coleta (média dos cores) |
| MEM% | Memória usada (%) no momento da coleta |
| SESSÕES | Sessões ativas totais no firewall (TCP+UDP+ICMP+SSL proxy) |
| SPEED (Mbps) | Velocidade nominal da interface |
| AVG/MAX IN/OUT (Mbps) | Média e pico da janela, por sentido, na RRA horária |
| PICO% | Pico (maior sentido) ÷ velocidade nominal |

"""

RODAPE = """\
## Instruções para o agente gerador do relatório executivo

1. Este arquivo contém **um bloco `## Site:` por Checkmk coletado** — trate cada
   um como um capítulo; consolide um sumário executivo cross-site no topo.
2. Destaques a extrair por site: firewalls com CPU≥70% ou MEM≥80%; interfaces
   com PICO%≥70 (risco de saturação); pares HA com passivo divergente
   (ex.: passivo com sessões > 0 pode indicar split-brain); hosts em
   `Sem coleta` (gap de monitoração — listar como pendência).
3. As tabelas de banda listam interfaces com pico ≥ 1 Mbps; o inventário
   completo (incluindo interfaces sem tráfego) está no CSV referenciado no
   bloco do site — use-o para afirmar contagens totais.
4. Números instantâneos (CPU/Mem/Sessões) são um snapshot — no texto, sempre
   citar o timestamp da coleta do bloco. Banda é janela de N dias (no bloco).
5. Formato sugerido do relatório final: sumário executivo → tabela consolidada
   por site → capítulos por site (consumo, banda, achados) → pendências.
"""


def fmt(v, nd=0):
    if v in (None, ""):
        return "-"
    return f"{float(v):,.{nd}f}"


def bloco_site(
    site_id: str, consumo: dict, banda: list[dict], dias: int, csv_ref: str
) -> str:
    ts = datetime.now(BRT).strftime("%Y-%m-%d %H:%M %Z")
    fws = consumo["firewalls"]
    sem = consumo.get("sem_coleta", [])

    linhas = [
        f"## Site: {site_id}",
        "",
        f"- **Coletado em:** {ts}",
        f"- **Janela de banda:** últimos {dias} dias (RRA 1h)",
        (
            f"- **Firewalls:** {len(fws)} · **Sem coleta:** "
            f"{', '.join(sem) if sem else 'nenhum'}"
        ),
        (
            f"- **CSV completo de interfaces:** `{csv_ref}` "
            f"({len(banda)} interfaces mapeadas)"
        ),
        "",
        "### Consumo instantâneo (CPU · Memória · Sessões)",
        "",
        "| Firewall | CPU % | MEM % | Sessões ativas |",
        "|---|---:|---:|---:|",
    ]
    for x in fws:
        linhas.append(
            f"| {x['firewall']} | {fmt(x['cpu'], 1)} | "
            f"{fmt(x['mem'], 1)} | {fmt(x['ses'])} |"
        )

    linhas += [
        "",
        f"### Banda por interface — {dias} dias (Mbps)",
        "",
        (
            "Interfaces com pico ≥ 1 Mbps, ordenadas pelo maior pico. "
            "Inventário completo no CSV."
        ),
        "",
        "| Firewall | Interface | Speed | Avg In | Max In | Avg Out | Max Out | Pico % |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    ativos = [
        r
        for r in banda
        if (r["max_in_mbps"] and float(r["max_in_mbps"]) >= 1)
        or (r["max_out_mbps"] and float(r["max_out_mbps"]) >= 1)
    ]
    ativos.sort(
        key=lambda r: -max(float(r["max_in_mbps"] or 0), float(r["max_out_mbps"] or 0))
    )
    for r in ativos:
        linhas.append(
            f"| {r['firewall']} | {r['interface']} | {fmt(r['speed_mbps'])} | "
            f"{fmt(r['avg_in_mbps'])} | {fmt(r['max_in_mbps'])} | "
            f"{fmt(r['avg_out_mbps'])} | {fmt(r['max_out_mbps'])} | "
            f"{fmt(r['util_pico_pct'])} |"
        )

    # resumo por firewall: nº de interfaces, com tráfego, pico agregado
    linhas += [
        "",
        "### Resumo de interfaces por firewall",
        "",
        "| Firewall | Interfaces mapeadas | Com tráfego (≥1 Mbps) | Maior pico (Mbps) | Interface do pico |",
        "|---|---:|---:|---:|---|",
    ]
    por_fw: dict[str, list[dict]] = {}
    for r in banda:
        por_fw.setdefault(r["firewall"], []).append(r)
    for fw in sorted(por_fw):
        rs = por_fw[fw]
        com_traf = [
            r
            for r in rs
            if (r["max_in_mbps"] and float(r["max_in_mbps"]) >= 1)
            or (r["max_out_mbps"] and float(r["max_out_mbps"]) >= 1)
        ]
        pico, pico_if = 0.0, "-"
        for r in rs:
            p = max(float(r["max_in_mbps"] or 0), float(r["max_out_mbps"] or 0))
            if p > pico:
                pico, pico_if = p, r["interface"]
        linhas.append(
            f"| {fw} | {len(rs)} | {len(com_traf)} | {fmt(pico)} | {pico_if} |"
        )
    linhas.append("")
    return "\n".join(linhas)


def main() -> int:
    site_id, consumo_p, banda_p, dias, md_p = sys.argv[1:6]
    with open(consumo_p) as f:
        consumo = json.load(f)
    with open(banda_p) as f:
        banda = list(csv.DictReader(f))
    novo = bloco_site(site_id, consumo, banda, int(dias), banda_p)

    md = Path(md_p)
    texto = md.read_text() if md.exists() else CABECALHO + RODAPE
    marca = f"## Site: {site_id}"
    if marca in texto:
        # substitui o bloco existente do site (até o próximo ## ou o rodapé)
        padrao = re.compile(
            rf"^## Site: {re.escape(site_id)}$.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL
        )
        texto = padrao.sub(novo + "\n", texto)
    else:
        # insere antes do rodapé
        texto = texto.replace(
            "## Instruções para o agente gerador",
            novo + "\n## Instruções para o agente gerador",
        )
    md.write_text(texto)
    print(
        f"{md_p}: bloco '{site_id}' atualizado "
        f"({len(consumo['firewalls'])} FWs, {len(banda)} interfaces)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CITADEL · NSX — as consultas Flux prontas do read-model de T1.

Decisões vindas da validação de 25/08/2026 (docs/validacao-nsx-t1-25-08.md):

- ``nsx_t1_totals`` está no bucket ``nsx`` (default do collector), NÃO no
  ``nsx_capacity`` onde ficam per_t0/per_vrf/nsx_capacity. Os painéis Grafana
  de total consultam o bucket errado; aqui lemos de onde o dado está. Se o
  collector mudar de bucket, troque ``BUCKET_TOTALS`` para ``bucket_capacity``.
- ``last()`` + ``pivot`` exige tipos homogêneos: ``limit``/``t1_count`` são
  long e ``usage_pct`` double → ``toFloat()`` antes do pivot, e o modelo
  converte de volta.
- Site sempre chega pelo regex de aliases (escapado) — nunca cru na query.
"""

from __future__ import annotations

from typing import Any

from .artefatos import snapshots_criacao
from .client import InfluxClient
from .config import Aliases
from .modelos import EventoT1, PontoHistorico, ResumoSite, T1PorT0, T1PorVrf

JANELA_ULTIMO = "-15m"  # 3 ciclos de capacity (intervals.slow = 5m)
# Premissa de arquitetura: 600 T1 por T0 (par de edge nodes), contando direto + VRFs.
# O limit de 1000 que o collector grava em nsx_t1_per_t0 vale só para os diretos.
T0_T1_LIMIT = 600
VRF_T1_LIMIT = 200  # premissa por VRF (o collector grava o mesmo valor em nsx_t1_per_vrf.limit)
T0_DIRECT_T1_LIMIT = 200  # T1 pendurados direto no T0 têm o mesmo teto de uma VRF


def _i(v: Any) -> int | None:
    return None if v is None else int(round(float(v)))


def _f(v: Any) -> float | None:
    return None if v is None else round(float(v), 2)


def _filtro_site(aliases: Aliases, site: str | None) -> str:
    if not site:
        return ""
    return f"  |> filter(fn: (r) => r.site =~ /{aliases.regex(site)}/)\n"


def flux_totals(
    bucket: str, aliases: Aliases, site: str | None, janela: str = JANELA_ULTIMO
) -> str:
    return (
        f'from(bucket: "{bucket}")\n'
        f"  |> range(start: {janela})\n"
        '  |> filter(fn: (r) => r._measurement == "nsx_t1_totals")\n'
        f"{_filtro_site(aliases, site)}"
        "  |> last() |> toFloat()\n"
        '  |> pivot(rowKey: ["site","_time"], columnKey: ["_field"], valueColumn: "_value")\n'
        '  |> keep(columns: ["_time","site","total","on_vrf","on_t0"])\n'
    )


def flux_capacity_t1(
    bucket: str, aliases: Aliases, site: str | None, janela: str = JANELA_ULTIMO
) -> str:
    return (
        f'from(bucket: "{bucket}")\n'
        f"  |> range(start: {janela})\n"
        '  |> filter(fn: (r) => r._measurement == "nsx_capacity" '
        'and r.usage_type == "NUMBER_OF_TIER1_ROUTERS")\n'
        f"{_filtro_site(aliases, site)}"
        "  |> last() |> toFloat()\n"
        '  |> pivot(rowKey: ["site","_time"], columnKey: ["_field"], valueColumn: "_value")\n'
        '  |> keep(columns: ["_time","site","current_usage","max_supported","usage_pct"])\n'
    )


def flux_per_t0(bucket: str, aliases: Aliases, site: str, janela: str = JANELA_ULTIMO) -> str:
    return (
        f'from(bucket: "{bucket}")\n'
        f"  |> range(start: {janela})\n"
        '  |> filter(fn: (r) => r._measurement == "nsx_t1_per_t0")\n'
        f"{_filtro_site(aliases, site)}"
        "  |> last() |> toFloat()\n"
        '  |> pivot(rowKey: ["site","t0_name","t0_id","_time"], '
        'columnKey: ["_field"], valueColumn: "_value")\n'
        '  |> keep(columns: ["_time","site","t0_name","t0_id",'
        '"t1_count","limit","usage_pct","available"])\n'
        '  |> group() |> sort(columns: ["usage_pct"], desc: true)\n'
    )


def flux_per_vrf(bucket: str, aliases: Aliases, site: str, janela: str = JANELA_ULTIMO) -> str:
    return (
        f'from(bucket: "{bucket}")\n'
        f"  |> range(start: {janela})\n"
        '  |> filter(fn: (r) => r._measurement == "nsx_t1_per_vrf")\n'
        f"{_filtro_site(aliases, site)}"
        "  |> last() |> toFloat()\n"
        '  |> pivot(rowKey: ["site","vrf_name","vrf_id","t0_parent","_time"], '
        'columnKey: ["_field"], valueColumn: "_value")\n'
        '  |> keep(columns: ["_time","site","vrf_name","vrf_id","t0_parent",'
        '"t1_count","limit","usage_pct","available"])\n'
        '  |> group() |> sort(columns: ["usage_pct"], desc: true)\n'
    )


def flux_historico(bucket: str, aliases: Aliases, site: str, dias: int) -> str:
    return (
        f'from(bucket: "{bucket}")\n'
        f"  |> range(start: -{int(dias)}d)\n"
        '  |> filter(fn: (r) => r._measurement == "nsx_t1_totals" and r._field == "total")\n'
        f"{_filtro_site(aliases, site)}"
        '  |> group(columns: ["_field"])\n'
        "  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)\n"
        '  |> keep(columns: ["_time","_value"])\n'
    )


def flux_eventos(bucket: str, aliases: Aliases, site: str, dias: int) -> str:
    return (
        f'from(bucket: "{bucket}")\n'
        f"  |> range(start: -{int(dias)}d)\n"
        '  |> filter(fn: (r) => r._measurement == "nsx_t1_event")\n'
        f"{_filtro_site(aliases, site)}"
        "  |> toFloat()\n"
        '  |> pivot(rowKey: ["_time","site","event","t1_id","t1_name",'
        '"vrf_name","edge_cluster_name"], '
        'columnKey: ["_field"], valueColumn: "_value")\n'
        '  |> keep(columns: ["_time","site","event","t1_id","t1_name","vrf_name",'
        '"edge_cluster_name","site_t1_total"])\n'
        '  |> group() |> sort(columns: ["_time"], desc: true)\n'
    )


class Consultas:
    """Fachada: cliente + buckets + aliases → modelos já normalizados."""

    def __init__(self, client: InfluxClient, aliases: Aliases):
        self.c, self.aliases = client, aliases
        self.b_nsx = client.cfg.bucket_nsx
        self.b_cap = client.cfg.bucket_capacity
        # ver docstring do módulo — totals vive no bucket default do collector
        self.b_totals = self.b_nsx

    def resumo(self, site: str | None = None) -> list[ResumoSite]:
        por_site: dict[str, dict[str, Any]] = {}
        for r in self.c.query(flux_totals(self.b_totals, self.aliases, site)):
            canon = self.aliases.canonico(r["site"])
            d = por_site.setdefault(canon, {"site": canon, "variantes": set()})
            d["variantes"].add(r["site"])
            # variantes coexistindo (TESP06 antigo × TESP6 novo): vence a mais recente
            if (d.get("atualizado_em") or "") > (r.get("_time") or ""):
                continue
            d.update(
                total=_i(r.get("total")),
                on_vrf=_i(r.get("on_vrf")),
                on_t0=_i(r.get("on_t0")),
                atualizado_em=r.get("_time"),
            )
        for r in self.c.query(flux_capacity_t1(self.b_cap, self.aliases, site)):
            canon = self.aliases.canonico(r["site"])
            d = por_site.setdefault(canon, {"site": canon, "variantes": set()})
            d["variantes"].add(r["site"])
            d.update(
                nsx_current=_i(r.get("current_usage")),
                nsx_max=_i(r.get("max_supported")),
                nsx_pct=_f(r.get("usage_pct")),
            )
            d.setdefault("atualizado_em", r.get("_time"))
        out = []
        for canon in sorted(por_site):
            d = por_site[canon]
            d["variantes"] = sorted(d["variantes"])
            out.append(ResumoSite(**d))
        return out

    def por_t0(self, site: str) -> list[T1PorT0]:
        """União por T0: diretos (nsx_t1_per_t0) + VRFs filhas (t0_parent)."""
        linhas_t0 = self.c.query(flux_per_t0(self.b_cap, self.aliases, site))
        nomes_t0 = [r.get("t0_name") or "" for r in linhas_t0]
        via_vrf: dict[str, int] = {}
        for v in self.por_vrf(site, nomes_t0):
            via_vrf[v.t0_parent] = via_vrf.get(v.t0_parent, 0) + v.t1_count
        out = []
        for r in linhas_t0:
            nome = r.get("t0_name") or ""
            direto = _i(r.get("t1_count")) or 0
            total = direto + via_vrf.get(nome, 0)
            out.append(
                T1PorT0(
                    site=self.aliases.canonico(r["site"]),
                    t0_name=nome,
                    t0_id=r.get("t0_id") or "",
                    t1_count=total,
                    t1_direct=direto,
                    t1_via_vrf=via_vrf.get(nome, 0),
                    limit=T0_T1_LIMIT,
                    usage_pct=round(100.0 * total / T0_T1_LIMIT, 2),
                    available=max(0, T0_T1_LIMIT - total),
                    atualizado_em=r.get("_time"),
                )
            )
        return sorted(out, key=lambda t: -t.t1_count)

    def por_vrf(self, site: str, nomes_t0: list[str] | None = None) -> list[T1PorVrf]:
        """``t0_parent`` vem do collector, que o deduz pelo sufixo ``-vrf_`` do nome
        (capacity.go:181). VRFs fora do padrão (``T0-Cluster_1_FG3``,
        ``T0-Cluster_1_PA2``, ``…-Tenant_Shared-1``) chegam com "-": aqui o pai é
        inferido pelo prefixo do nome quando esse T0 existe no site, e a linha
        fica marcada ``parent_inferido=True``. Confirmado no TECE pelo
        nsx_ha_state (T1 filhos da FG3 no par do T0-Cluster_1)."""
        if nomes_t0 is None:
            nomes_t0 = [
                r.get("t0_name") or ""
                for r in self.c.query(flux_per_t0(self.b_cap, self.aliases, site))
            ]
        return [
            T1PorVrf(
                site=self.aliases.canonico(r["site"]),
                vrf_name=r.get("vrf_name") or "",
                vrf_id=r.get("vrf_id") or "",
                t0_parent=_pai(r.get("t0_parent"), r.get("vrf_name") or "", nomes_t0)[0],
                parent_inferido=_pai(r.get("t0_parent"), r.get("vrf_name") or "", nomes_t0)[1],
                t1_count=_i(r.get("t1_count")) or 0,
                limit=_i(r.get("limit")) or 0,
                usage_pct=_f(r.get("usage_pct")) or 0.0,
                available=_i(r.get("available")) or 0,
                atualizado_em=r.get("_time"),
            )
            for r in self.c.query(flux_per_vrf(self.b_cap, self.aliases, site))
        ]

    def historico(self, site: str, dias: int = 30) -> list[PontoHistorico]:
        return [
            PontoHistorico(quando=r["_time"], total=_i(r.get("_value")))
            for r in self.c.query(flux_historico(self.b_totals, self.aliases, site, dias))
        ]

    def eventos(self, site: str, dias: int = 7) -> list[EventoT1]:
        return [
            EventoT1(
                site=self.aliases.canonico(r["site"]),
                quando=r["_time"],
                event=r.get("event") or "",
                t1_name=r.get("t1_name") or "",
                t1_id=r.get("t1_id") or "",
                parent_name=r.get("vrf_name") or "",
                edge_cluster_name=r.get("edge_cluster_name") or "",
                site_t1_total=_i(r.get("site_t1_total")),
            )
            for r in self.c.query(flux_eventos(self.b_nsx, self.aliases, site, dias))
        ]

    def tabela(self, site: str | None = None) -> list[dict]:
        """Linhas no formato da planilha de capacity (uma por VRF, mais uma por T0
        com os T1 diretos): Edge · Node · Limite-node · vrf-number · limite-vrf ·
        Dia · Mes · Ano · Qtd-vrf."""
        resumos = {r.site: r for r in self.resumo(site)}
        sites = [site] if site else sorted(resumos)
        out: list[dict] = []
        for s_ in sites:
            total_edge = resumos[s_].total if s_ in resumos else None
            # agrupado por T0 em ordem natural (Cluster_1, Cluster_2, …), não por uso
            for t in sorted(self.por_t0(s_), key=lambda t: _natural(t.t0_name)):
                dia, mes, ano = _dma(t.atualizado_em)
                out.append(
                    {
                        "edge": s_,
                        "node": t.t0_name,
                        "limite_node": T0_T1_LIMIT,
                        "vrf": "(direto no T0)",
                        "limite_vrf": T0_DIRECT_T1_LIMIT,
                        "dia": dia,
                        "mes": mes,
                        "ano": ano,
                        "qtd": t.t1_direct,
                        "qtd_node": t.t1_count,
                        "total_edge": total_edge,
                    }
                )
                for v in sorted(self.por_vrf(s_), key=lambda v: _natural(v.vrf_name)):
                    if v.t0_parent != t.t0_name:
                        continue
                    dia, mes, ano = _dma(v.atualizado_em)
                    out.append(
                        {
                            "edge": s_,
                            "node": t.t0_name,
                            "limite_node": None,  # só na linha "(direto no T0)", para não confundir
                            "vrf": v.vrf_name,
                            "limite_vrf": v.limit or VRF_T1_LIMIT,
                            "dia": dia,
                            "mes": mes,
                            "ano": ano,
                            "qtd": v.t1_count,
                            "qtd_node": t.t1_count,
                            "total_edge": total_edge,
                        }
                    )
            for v in self.por_vrf(s_):
                if any(t.t0_name == v.t0_parent for t in self.por_t0(s_)):
                    continue
                dia, mes, ano = _dma(v.atualizado_em)
                out.append(
                    {
                        "edge": s_,
                        "node": v.t0_parent or "-",
                        "limite_node": None,
                        "vrf": v.vrf_name,
                        "limite_vrf": v.limit or VRF_T1_LIMIT,
                        "dia": dia,
                        "mes": mes,
                        "ano": ano,
                        "qtd": v.t1_count,
                        "qtd_node": None,
                        "total_edge": total_edge,
                    }
                )
        return out


def _natural(nome: str) -> list:
    """Chave de ordenação natural: 'T0-Cluster_10' depois de 'T0-Cluster_2'."""
    import re as _re

    return [int(x) if x.isdigit() else x.lower() for x in _re.split(r"(\d+)", nome)]


def _pai(t0_parent: str | None, vrf_name: str, nomes_t0: list[str]) -> tuple[str, bool]:
    """(pai, inferido). Pai do collector se veio; senão o T0 mais longo que é
    prefixo do nome da VRF."""
    if t0_parent and t0_parent != "-":
        return t0_parent, False
    candidatos = [n for n in nomes_t0 if n and vrf_name.startswith(n)]
    if not candidatos:
        return "-", False
    return max(candidatos, key=len), True


def _dma(iso: str | None) -> tuple[int | None, int | None, int | None]:
    if not iso or len(iso) < 10:
        return None, None, None
    return int(iso[8:10]), int(iso[5:7]), int(iso[0:4])


def crescimento_por_criacao(site: str, eventos: list[EventoT1] | None = None) -> dict | None:
    """Criados por mês pelo ``_create_time`` (snapshot mais recente da Manager) +
    removidos por mês (eventos do collector, só dentro da retenção) + os T1 que
    sumiram entre o snapshot anterior e o atual (remoções inferidas)."""
    import json as _json
    from collections import Counter

    snaps = snapshots_criacao(site)
    if not snaps:
        return None
    atual = _json.loads(snaps[-1].read_text(encoding="utf-8"))
    criados: Counter[str] = Counter()
    for t in atual["t1s"]:
        if t.get("create_time"):
            criados[t["create_time"][:7]] += 1
    removidos_ev: Counter[str] = Counter()
    for e in eventos or []:
        if e.event == "deleted":
            removidos_ev[e.quando[:7]] += 1
    sumiram: list[dict] = []
    if len(snaps) >= 2:
        anterior = _json.loads(snaps[-2].read_text(encoding="utf-8"))
        ids_atual = {t["id"] for t in atual["t1s"]}
        sumiram = [t for t in anterior["t1s"] if t["id"] not in ids_atual]
    meses = sorted(set(criados) | set(removidos_ev))
    acumulado, linhas = 0, []
    for m in meses:
        acumulado += criados[m]
        linhas.append(
            {
                "mes": m,
                "criados": criados[m],
                "removidos": removidos_ev.get(m, 0),
                "acumulado_criados": acumulado,
            }
        )
    # média dos últimos 3 meses fechados (o mês corrente entra parcial, fica de fora)
    corrente = atual["gerado_em"][:7]
    fechados = [x for x in linhas if x["mes"] < corrente][-3:]
    media3 = round(sum(x["criados"] for x in fechados) / len(fechados), 1) if fechados else None
    return {
        "site": site,
        "snapshot": atual["gerado_em"],
        "snapshots": len(snaps),
        "total_t1": atual["total"],
        "primeiro_t1": atual["t1s"][0]["create_time"] if atual["t1s"] else None,
        "media_criados_3m": media3,
        "meses_fechados_na_media": [x["mes"] for x in fechados],
        "sumiram_desde_snapshot_anterior": len(sumiram),
        "sumiram": [{"name": t["name"], "create_time": t["create_time"]} for t in sumiram[:50]],
        "por_mes": linhas,
    }

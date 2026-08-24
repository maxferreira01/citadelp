"""CITADEL · ACI — descoberta de qual site Checkmk monitora quais leafs.

Não existe inventário disso: descobrimos consultando cada site (GET hosts) em
vez de assumir. O ``cmk_site`` do config do fabric é a fonte de verdade de ONDE
a regra será criada; a descoberta VALIDA — e acusa quando um leaf não está lá,
está com outro nome, ou aparece em mais de um site (a colisão conhecida
mk_tece1/mk_tesp2, mesmo IP 172.18.162.11).

O matching de hostname é tolerante porque o parque tem inconsistências reais:
``LEAF1017TESP07`` (zero a mais) num fabric onde os demais são ``TESP7``, e
leafs nomeados ``TBSP2`` dentro do fabric TESP2. Nada de match "na fé": cada
camada registra evidência, e leaf sem match NUNCA entra em regra (fica
alarmando, que é o lado seguro).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import httpx

from ..checkmk.gateway import CheckmkError, Gateway, Site

RE_LEAF = re.compile(r"^LEAF0*(\d+)([A-Z]+?)0*(\d*)$", re.IGNORECASE)


def normalizar_leaf(nome: str) -> tuple[str, str] | None:
    """``LEAF1017TESP07`` → ("1017", "TESP7"); None se não parecer leaf.

    Normaliza zeros à esquerda tanto no número do leaf quanto no sufixo
    numérico do site — é isso que faz TESP03/TESP3 e TESP07/TESP7 casarem.
    """
    m = RE_LEAF.match(nome.strip().upper())
    if not m:
        return None
    numero, site_txt, site_num = m.groups()
    return numero, site_txt + (site_num.lstrip("0") if site_num else "")


@dataclass
class SiteDescoberto:
    site_id: str
    versao: str = ""
    sem_rest: bool = False
    erro: str = ""
    hosts_leaf: list[str] = field(default_factory=list)


@dataclass
class MatchLeaf:
    leaf_aci: str
    host_cmk: str | None
    site_id: str | None
    camada: str  # exato | normalizado | numero-unico | sem-match
    confianca: str  # alta | media | -
    detalhe: str = ""


def descobrir_sites(
    sites: dict[str, Site], transport: httpx.BaseTransport | None = None
) -> dict[str, SiteDescoberto]:
    """Versão + hosts LEAF* de cada site. Site fora do ar vira registro de erro."""
    out: dict[str, SiteDescoberto] = {}
    for sid, site in sites.items():
        d = SiteDescoberto(site_id=sid)
        gw = Gateway(site, transport=transport)
        try:
            try:
                v = gw.get_version()
                d.versao = v.get("versions", {}).get("checkmk", "")
            except CheckmkError as exc:
                if exc.status == 404:
                    # REST API inexistente = Checkmk 1.5 (fluxo manual)
                    d.sem_rest = True
                    out[sid] = d
                    continue
                raise
            d.hosts_leaf = sorted(
                h["id"] for h in gw.list_hosts() if h["id"] and RE_LEAF.match(h["id"].upper())
            )
        except CheckmkError as exc:
            d.erro = str(exc)
        finally:
            gw.close()
        out[sid] = d
    return out


def casar_leafs(
    leafs_aci: list[str],
    descobertos: dict[str, SiteDescoberto],
    site_esperado: str,
) -> list[MatchLeaf]:
    """Casa cada leaf do fabric com um host Checkmk, em camadas com evidência.

    1. nome exato no site esperado;
    2. par normalizado (número + site sem zeros) no site esperado;
    3. número do leaf único no site esperado (cobre os TBSP2 dentro do TESP2)
       — confiança média, listado para revisão.
    Host achado TAMBÉM em outro site → vira detalhe de colisão no match.
    """
    esperado = descobertos.get(site_esperado)
    hosts = esperado.hosts_leaf if esperado else []
    por_norm: dict[tuple[str, str], list[str]] = {}
    por_numero: dict[str, list[str]] = {}
    for h in hosts:
        n = normalizar_leaf(h)
        if n:
            por_norm.setdefault(n, []).append(h)
            por_numero.setdefault(n[0], []).append(h)

    outros_sites: dict[str, list[str]] = {}
    for sid, d in descobertos.items():
        if sid == site_esperado:
            continue
        for h in d.hosts_leaf:
            outros_sites.setdefault(h.upper(), []).append(sid)

    out: list[MatchLeaf] = []
    hosts_upper = {h.upper(): h for h in hosts}
    for leaf in leafs_aci:
        m: MatchLeaf
        norm = normalizar_leaf(leaf)
        if leaf.upper() in hosts_upper:
            m = MatchLeaf(leaf, hosts_upper[leaf.upper()], site_esperado, "exato", "alta")
        elif norm and len(por_norm.get(norm, [])) == 1:
            m = MatchLeaf(leaf, por_norm[norm][0], site_esperado, "normalizado", "alta")
        elif norm and len(por_numero.get(norm[0], [])) == 1:
            m = MatchLeaf(
                leaf,
                por_numero[norm[0]][0],
                site_esperado,
                "numero-unico",
                "media",
                detalhe="casou só pelo número do leaf — revisar",
            )
        else:
            candidatos = por_numero.get(norm[0], []) if norm else []
            m = MatchLeaf(
                leaf,
                None,
                None,
                "sem-match",
                "-",
                detalhe=(
                    f"ambíguo entre {candidatos}" if len(candidatos) > 1 else "não está no site"
                ),
            )
        if m.host_cmk and m.host_cmk.upper() in outros_sites:
            m.detalhe = (
                f"{m.detalhe + ' | ' if m.detalhe else ''}"
                f"COLISÃO: host também em {outros_sites[m.host_cmk.upper()]}"
            )
        out.append(m)
    return out

"""CITADEL · ACI — modelos de dados do mapa de portas e parsers de DN.

Os DNs do APIC carregam a localização (pod/node/interface) embutida no texto;
os regexes aqui cobrem as duas formas que aparecem nos objetos que usamos:
``.../sys/phys-[eth1/33]/...`` (l1PhysIf, ethpmPhysIf) e ``.../if-[eth1/53]/...``
(lldpAdjEp). Para o binding EPG→porta (fvRsPathAtt), só o path DIRETO
(``paths-<node>/pathep-[eth1/x]``) resolve para porta física; paths de VPC
(``protpaths-A-B/pathep-[<policy-group>]``) apontam para policy group e ficam
de fora — o sinal de acesso nesses casos vem de usage/bundle/LLDP/descr.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

RE_DN_NODE = re.compile(r"topology/pod-(\d+)/node-(\d+)/")
RE_DN_IFACE = re.compile(r"\[([^\]]+)\]")
RE_EPG = re.compile(r"uni/tn-([^/]+)/ap-([^/]+)/epg-([^/]+)")
RE_TDN_PATH_DIRETO = re.compile(r"topology/pod-(\d+)/paths-(\d+)/pathep-\[([^\]]+)\]")


def parse_dn(dn: str) -> tuple[str, str, str]:
    """Extrai (pod, node_id, iface) de um DN de topology; vazios se não casar."""
    m = RE_DN_NODE.search(dn)
    if not m:
        return "", "", ""
    i = RE_DN_IFACE.search(dn)
    return m.group(1), m.group(2), i.group(1) if i else ""


def parse_path_att(dn: str, t_dn: str) -> tuple[str, str, str, str] | None:
    """(tenant/ap/epg, pod, node_id, iface) de um fvRsPathAtt de path direto."""
    epg = RE_EPG.search(dn)
    alvo = RE_TDN_PATH_DIRETO.search(t_dn)
    if not epg or not alvo:
        return None
    nome_epg = f"{epg.group(1)}/{epg.group(2)}/{epg.group(3)}"
    return nome_epg, alvo.group(1), alvo.group(2), alvo.group(3)


def chave_iface(pod: str, node_id: str, iface: str) -> str:
    """Chave canônica de join entre datasets por porta (mesma do coletor Go)."""
    return f"{pod}/{node_id}/{iface}"


class ClassePorta(StrEnum):
    UPLINK_FABRIC = "uplink_fabric"  # leaf → spine
    UPLINK_APIC = "uplink_apic"  # leaf → controller APIC
    NSX_EDGE = "nsx_edge"
    FIREWALL = "firewall"
    ROTEADOR = "roteador"  # RT01/RT02 — borda internet/WAN
    SW_GERENCIA = "sw_gerencia"
    ACESSO_SERVIDOR = "acesso_servidor"
    LIVRE = "livre"
    DESCONHECIDA = "desconhecida"


# As únicas classes que autorizam silenciar notificação. DESCONHECIDA fica de
# fora de propósito: na dúvida a porta continua alarmando (fail-safe).
CLASSES_SILENCIAVEIS = frozenset({ClassePorta.ACESSO_SERVIDOR, ClassePorta.LIVRE})


@dataclass(frozen=True)
class NoFabric:
    pod: str
    node_id: str
    name: str
    role: str  # leaf | spine | controller
    address: str  # mgmt IP (TEP nos controllers antigos — usar com o nome junto)
    model: str
    serial: str


@dataclass(frozen=True)
class VizinhoLLDP:
    sys_name: str
    sys_desc: str
    mgmt_ip: str
    chassis_id: str
    port_id: str
    port_desc: str
    capability: str

    @property
    def nome_curto(self) -> str:
        """sysName sem o domínio (LLDP costuma anunciar FQDN)."""
        return self.sys_name.split(".", 1)[0] if self.sys_name else ""


@dataclass
class PortaFisica:
    """Uma porta física de leaf com tudo que os datasets do APIC dizem dela."""

    pod: str
    node_id: str
    leaf_name: str
    iface: str  # eth1/33
    admin_st: str = ""
    descr: str = ""
    mode: str = ""  # trunk | access | ...
    usage: str = ""  # epg | infra | discovery | blacklist | fabric (lista com vírgula)
    oper_st: str = ""
    oper_speed: str = ""
    oper_reason: str = ""  # ethpmPhysIf.operStQual (sfp-missing, link-failure...)
    bundle: str = ""  # ethpmPhysIf.bundleIndex (po22) ou "" quando fora de LAG
    last_link_chg: str = ""
    lldp: VizinhoLLDP | None = None
    epgs: list[str] = field(default_factory=list)

    @property
    def esta_up(self) -> bool:
        return self.oper_st == "up"


@dataclass
class Classificacao:
    classe: ClassePorta
    confianca: str  # alta | media | baixa
    evidencia: list[str] = field(default_factory=list)

    @property
    def silenciar(self) -> bool:
        return self.classe in CLASSES_SILENCIAVEIS


@dataclass
class PortaMapeada:
    porta: PortaFisica
    cls: Classificacao

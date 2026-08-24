"""CITADEL · ACI — classificação de porta de leaf (funções puras).

A pergunta que este módulo responde, porta a porta: "se este link cair às 3h,
alguém precisa acordar?" — uplink de fabric/APIC, NSX edge, firewall e switch de
gerência SIM (mantêm alarme); acesso de servidor e porta livre NÃO (candidatas a
silenciar notificação no Checkmk). Tudo que não for POSITIVAMENTE identificado
sai como DESCONHECIDA, que também mantém alarme — o erro barato é alarmar demais.

Ordem dos sinais (do mais ao menos confiável):
1. Identidade do vizinho LLDP contra o fabricNode (spines/controllers por
   mgmtIp E nome curto) — nunca por número de porta: leafs N9K-C93600CD-GX
   fazem uplink em eth1/35-36, não em eth1/49-54.
2. Vizinho LLDP por padrão de dispositivo (FW, SW99, NSX edge, servidor ESX).
   Exceção: NIC Broadcom anuncia LLDP próprio ("Broadcom Adv. Quad 25Gb...")
   sem identificar o host — nesse caso o LLDP NÃO decide, só vira evidência.
3. descr da porta (convenções humanas reais do parque: "LIVRE",
   "RESERVADA ... EXPANSÃO LAG NSX", "TESP3ESX1P00013 - vmnic0", "SW99...").
4. usage + estado físico (epg/discovery/blacklist/fabric + oper_reason).
5. Número da porta NUNCA classifica — no máximo entra como observação.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .modelos import ClassePorta, Classificacao, NoFabric, PortaFisica, PortaMapeada

# oper_reason (ethpmPhysIf.operStQual) que caracteriza porta morta — mesmo
# critério do survey de portas livres.
MOTIVOS_PORTA_MORTA = frozenset({"sfp-missing", "link-failure", "link-not-connected", "admin-down"})

RE_FIREWALL = re.compile(r"^FW\d", re.IGNORECASE)
RE_ROTEADOR = re.compile(r"^RT\d", re.IGNORECASE)
RE_SW_GERENCIA = re.compile(r"^SW99", re.IGNORECASE)
RE_NSX_DEFAULT = re.compile(r"nsx|edge", re.IGNORECASE)
# hostname de servidor do parque: TESP3ESX1P00013, tesp6cmk1p00001...
RE_SERVIDOR = re.compile(r"esx|vmnic|\dP\d{5}", re.IGNORECASE)
RE_NIC_SEM_HOST = re.compile(r"broadcom|qlogic|mellanox|intel.*ethernet", re.IGNORECASE)
RE_DESCR_LIVRE = re.compile(r"\bLIVRE\b", re.IGNORECASE)
RE_DESCR_NSX = re.compile(r"\bNSX\b|LAG[ _-]?NSX", re.IGNORECASE)
RE_APIC = re.compile(r"^apic", re.IGNORECASE)


@dataclass
class ContextoFabric:
    """Identidades de infraestrutura do fabric, extraídas do fabricNode."""

    spines_nomes: frozenset[str]
    spines_ips: frozenset[str]
    controllers_nomes: frozenset[str]
    controllers_ips: frozenset[str]
    padrao_nsx: re.Pattern = field(default_factory=lambda: RE_NSX_DEFAULT)

    @classmethod
    def de_nos(cls, nos: list[NoFabric], padrao_nsx: str | None = None) -> ContextoFabric:
        return cls(
            spines_nomes=frozenset(n.name for n in nos if n.role == "spine" and n.name),
            spines_ips=frozenset(n.address for n in nos if n.role == "spine" and n.address),
            controllers_nomes=frozenset(n.name for n in nos if n.role == "controller" and n.name),
            controllers_ips=frozenset(
                n.address for n in nos if n.role == "controller" and n.address
            ),
            padrao_nsx=re.compile(padrao_nsx, re.IGNORECASE) if padrao_nsx else RE_NSX_DEFAULT,
        )


def _vizinho_esta_em(nome: str, ip: str, nomes: frozenset[str], ips: frozenset[str]) -> bool:
    if ip and ip != "unspecified" and ip in ips:
        return True
    return bool(nome) and nome in nomes


def classificar_porta(p: PortaFisica, ctx: ContextoFabric) -> Classificacao:
    ev: list[str] = []
    usage = {u.strip() for u in p.usage.split(",") if u.strip()}

    # --- 1-2. vizinho LLDP
    if p.lldp is not None:
        nome = p.lldp.nome_curto
        ev.append(f"lldp={nome or p.lldp.chassis_id}")
        if _vizinho_esta_em(nome, p.lldp.mgmt_ip, ctx.spines_nomes, ctx.spines_ips):
            return Classificacao(ClassePorta.UPLINK_FABRIC, "alta", ev + ["vizinho=spine"])
        if _vizinho_esta_em(
            nome, p.lldp.mgmt_ip, ctx.controllers_nomes, ctx.controllers_ips
        ) or RE_APIC.search(nome):
            return Classificacao(ClassePorta.UPLINK_APIC, "alta", ev + ["vizinho=apic"])
        texto_viz = f"{nome} {p.lldp.sys_desc}"
        if RE_NIC_SEM_HOST.search(texto_viz) and not RE_SERVIDOR.search(nome):
            # NIC que fala LLDP por conta própria: não identifica o host.
            ev.append("lldp-de-nic-nao-decide")
        elif RE_FIREWALL.search(nome) or re.search(
            r"palo alto|fortigate", p.lldp.sys_desc, re.IGNORECASE
        ):
            return Classificacao(ClassePorta.FIREWALL, "alta", ev + ["vizinho=firewall"])
        elif RE_ROTEADOR.search(nome):
            return Classificacao(ClassePorta.ROTEADOR, "alta", ev + ["vizinho=roteador"])
        elif RE_SW_GERENCIA.search(nome):
            return Classificacao(ClassePorta.SW_GERENCIA, "alta", ev + ["vizinho=sw99"])
        elif ctx.padrao_nsx.search(nome):
            return Classificacao(ClassePorta.NSX_EDGE, "alta", ev + ["vizinho=nsx-edge"])
        elif RE_SERVIDOR.search(nome):
            return Classificacao(ClassePorta.ACESSO_SERVIDOR, "alta", ev + ["vizinho=servidor"])
        elif nome:
            # Tem ALGUÉM identificável do outro lado e nós não sabemos quem é.
            # Foi assim que RT01/RT02 (roteadores de borda) quase viraram
            # "acesso" no piloto — vizinho nomeado e não reconhecido NUNCA
            # desce para os sinais mais fracos: fica DESCONHECIDA (alarma).
            return Classificacao(
                ClassePorta.DESCONHECIDA, "media", ev + ["vizinho-nao-reconhecido"]
            )

    # --- 3. descr (convenção humana)
    if p.descr:
        ev.append(f"descr={p.descr[:60]}")
        if RE_DESCR_LIVRE.search(p.descr):
            if not p.esta_up:
                return Classificacao(ClassePorta.LIVRE, "alta", ev + ["descr=LIVRE, porta down"])
            ev.append("descr-diz-LIVRE-mas-porta-up")  # descr mentindo: não decide
        elif RE_DESCR_NSX.search(p.descr):
            if p.esta_up:
                return Classificacao(ClassePorta.NSX_EDGE, "media", ev + ["descr=NSX, porta up"])
            return Classificacao(ClassePorta.LIVRE, "media", ev + ["descr=reserva NSX, porta down"])
        elif RE_SW_GERENCIA.search(p.descr.replace(" ", "")):
            return Classificacao(ClassePorta.SW_GERENCIA, "media", ev + ["descr=SW99"])
        elif RE_FIREWALL.search(p.descr):
            return Classificacao(ClassePorta.FIREWALL, "media", ev + ["descr=firewall"])
        elif RE_ROTEADOR.search(p.descr):
            return Classificacao(ClassePorta.ROTEADOR, "media", ev + ["descr=roteador"])
        elif RE_SERVIDOR.search(p.descr):
            return Classificacao(ClassePorta.ACESSO_SERVIDOR, "media", ev + ["descr=servidor"])

    # --- 4. usage + estado físico
    if "fabric" in usage:
        return Classificacao(ClassePorta.UPLINK_FABRIC, "media", ev + ["usage=fabric"])
    if "blacklist" in usage:
        return Classificacao(ClassePorta.LIVRE, "alta", ev + ["usage=blacklist"])
    if "epg" in usage:
        ev.append("usage=epg")
        if p.epgs:
            ev.append(f"epgs={';'.join(p.epgs[:3])}")
        if p.esta_up:
            return Classificacao(ClassePorta.ACESSO_SERVIDOR, "media", ev)
        # porta de EPG down: configuração de acesso, sem tráfego — não é infra
        return Classificacao(ClassePorta.ACESSO_SERVIDOR, "baixa", ev + ["porta down"])
    if usage <= {"discovery"} and not p.esta_up and p.oper_reason in MOTIVOS_PORTA_MORTA:
        return Classificacao(ClassePorta.LIVRE, "alta", ev + [f"down: {p.oper_reason}"])

    ev.append(f"oper={p.oper_st or '?'}/{p.oper_reason or '?'}, usage={p.usage or '?'}")
    return Classificacao(ClassePorta.DESCONHECIDA, "baixa", ev)


# Ao agregar um port-channel, prevalece a classe mais "infra" entre os membros.
_PRIORIDADE_INFRA = [
    ClassePorta.UPLINK_FABRIC,
    ClassePorta.UPLINK_APIC,
    ClassePorta.FIREWALL,
    ClassePorta.ROTEADOR,
    ClassePorta.NSX_EDGE,
    ClassePorta.SW_GERENCIA,
    ClassePorta.DESCONHECIDA,
    ClassePorta.ACESSO_SERVIDOR,
    ClassePorta.LIVRE,
]


def agregar_port_channels(mapeadas: list[PortaMapeada]) -> list[PortaMapeada]:
    """Gera uma linha sintética por port-channel (po22 → "Interface port-channel22").

    O PC só é silenciável se TODOS os membros forem; um único membro
    infra/desconhecido mantém o alarme do agregado.
    """
    grupos: dict[tuple[str, str, str], list[PortaMapeada]] = {}
    for m in mapeadas:
        if m.porta.bundle:
            grupos.setdefault((m.porta.pod, m.porta.node_id, m.porta.bundle), []).append(m)

    out: list[PortaMapeada] = []
    for (pod, node_id, bundle), membros in sorted(grupos.items()):
        classe = min(membros, key=lambda m: _PRIORIDADE_INFRA.index(m.cls.classe)).cls.classe
        todos_silenciam = all(m.cls.silenciar for m in membros)
        ev = [f"membros={','.join(m.porta.iface for m in membros)}"]
        if not todos_silenciam and classe in (ClassePorta.ACESSO_SERVIDOR, ClassePorta.LIVRE):
            # mistura estranha (ex. acesso + desconhecida): não silenciar
            classe = ClassePorta.DESCONHECIDA
        p = PortaFisica(
            pod=pod,
            node_id=node_id,
            leaf_name=membros[0].porta.leaf_name,
            iface=bundle,
            oper_st="up" if any(m.porta.esta_up for m in membros) else "down",
            usage=membros[0].porta.usage,
        )
        confianca = "alta" if todos_silenciam or classe != ClassePorta.DESCONHECIDA else "baixa"
        out.append(PortaMapeada(p, Classificacao(classe, confianca, ev)))
    return out


def classificar_mapa(
    portas: list[PortaFisica], nos: list[NoFabric], padrao_nsx: str | None = None
) -> list[PortaMapeada]:
    ctx = ContextoFabric.de_nos(nos, padrao_nsx)
    mapeadas = [PortaMapeada(p, classificar_porta(p, ctx)) for p in portas]
    return mapeadas + agregar_port_channels(mapeadas)

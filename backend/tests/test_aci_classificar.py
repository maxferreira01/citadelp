"""Classificação de porta de leaf — os casos que definem a política.

Cada teste aqui é um caso real do parque encontrado nas auditorias/pilotos:
o uplink em eth1/35 (N9K-C93600CD-GX), a NIC Broadcom que fala LLDP sozinha,
os roteadores RT01/RT02 que quase viraram "acesso" no piloto do TESP6, e o
fail-safe central: na dúvida, a porta continua alarmando.
"""

from __future__ import annotations

from app.aci.classificar import ContextoFabric, agregar_port_channels, classificar_mapa
from app.aci.classificar import classificar_porta as cls
from app.aci.modelos import (
    ClassePorta,
    Classificacao,
    NoFabric,
    PortaFisica,
    PortaMapeada,
    VizinhoLLDP,
)

NOS = [
    NoFabric("1", "101", "SPINE101TESP6", "spine", "10.114.35.111", "N9K-C9364C", "S1"),
    NoFabric("1", "102", "SPINE102TESP6", "spine", "10.114.35.112", "N9K-C9364C", "S2"),
    NoFabric("1", "1", "APIC01TESP6", "controller", "10.0.0.1", "APIC-M3", "C1"),
    NoFabric("1", "1001", "LEAF1001TESP6", "leaf", "10.114.35.121", "N9K-C93600CD-GX", "L1"),
]
CTX = ContextoFabric.de_nos(NOS)


def porta(**kw) -> PortaFisica:
    base = dict(pod="1", node_id="1001", leaf_name="LEAF1001TESP6", iface="eth1/1")
    base.update(kw)
    return PortaFisica(**base)


def viz(sys_name="", sys_desc="", mgmt_ip="") -> VizinhoLLDP:
    return VizinhoLLDP(sys_name, sys_desc, mgmt_ip, "aa:bb", "Eth1/1", "", "bridge,router")


def test_uplink_por_identidade_do_vizinho_nao_por_numero_de_porta():
    # N9K-C93600CD-GX faz uplink em eth1/35 — o número da porta não pode pesar
    p = porta(
        iface="eth1/35", oper_st="up", usage="fabric", lldp=viz("SPINE101TESP6.tesp6infra.local")
    )
    r = cls(p, CTX)
    assert r.classe is ClassePorta.UPLINK_FABRIC
    assert r.confianca == "alta"
    assert not r.silenciar


def test_uplink_por_mgmt_ip_quando_sysname_nao_veio():
    p = porta(oper_st="up", lldp=viz("", "", "10.114.35.112"))
    assert cls(p, CTX).classe is ClassePorta.UPLINK_FABRIC


def test_apic_por_nome():
    p = porta(oper_st="up", usage="infra", lldp=viz("APIC01TESP6"))
    r = cls(p, CTX)
    assert r.classe is ClassePorta.UPLINK_APIC
    assert not r.silenciar


def test_roteador_de_borda_mantem_alarme():
    # caso real do piloto TESP6: RT01/RT02 com usage=epg quase viraram acesso
    p = porta(oper_st="up", usage="epg", lldp=viz("RT01TESP6"))
    r = cls(p, CTX)
    assert r.classe is ClassePorta.ROTEADOR
    assert not r.silenciar


def test_vizinho_nomeado_nao_reconhecido_nunca_silencia():
    p = porta(oper_st="up", usage="epg", lldp=viz("Pegasus01-e1b"))
    r = cls(p, CTX)
    assert r.classe is ClassePorta.DESCONHECIDA
    assert not r.silenciar


def test_nic_broadcom_nao_decide_mas_descr_de_servidor_sim():
    p = porta(
        oper_st="up",
        usage="epg",
        descr="TESP3ESX1P00013 - vmnic0 (Dados)",
        lldp=viz("b8:ca:3a:x", "Broadcom Adv. Quad 25Gb Ethernet fw_version:218.0.219.14"),
    )
    r = cls(p, CTX)
    assert r.classe is ClassePorta.ACESSO_SERVIDOR
    assert r.silenciar


def test_firewall_por_lldp_e_por_descr():
    assert cls(porta(oper_st="up", lldp=viz("FW01TESP6")), CTX).classe is ClassePorta.FIREWALL
    assert (
        cls(porta(oper_st="up", descr="FW01TESP6 (WAN) eth1/21-22"), CTX).classe
        is ClassePorta.FIREWALL
    )


def test_sw_gerencia():
    assert cls(porta(oper_st="up", lldp=viz("SW99TESP6")), CTX).classe is ClassePorta.SW_GERENCIA


def test_reserva_nsx_down_e_livre_up_e_nsx_edge():
    reservada = porta(descr="RESERVADA LEOPOLDO - EXPANSÃO LAG NSX 05/06", oper_st="down")
    assert cls(reservada, CTX).classe is ClassePorta.LIVRE
    ativa = porta(descr="NSX-Edge-NODE-7 - fp-eth0", oper_st="up", usage="epg")
    r = cls(ativa, CTX)
    assert r.classe is ClassePorta.NSX_EDGE
    assert not r.silenciar


def test_porta_livre_por_estado_morto():
    p = porta(usage="discovery", oper_st="down", oper_reason="sfp-missing")
    r = cls(p, CTX)
    assert r.classe is ClassePorta.LIVRE
    assert r.silenciar


def test_descr_livre_mas_porta_up_nao_silencia_por_descr():
    p = porta(descr="LIVRE", oper_st="up", usage="discovery")
    assert cls(p, CTX).classe is ClassePorta.DESCONHECIDA


def test_fail_safe_central_porta_sem_sinal_fica_desconhecida():
    p = porta(oper_st="up", usage="discovery")
    r = cls(p, CTX)
    assert r.classe is ClassePorta.DESCONHECIDA
    assert not r.silenciar  # na dúvida, alarma


def test_port_channel_so_silencia_com_todos_os_membros_silenciaveis():
    def m(iface, classe, bundle="po22"):
        return PortaMapeada(
            porta(iface=iface, bundle=bundle, oper_st="up"),
            Classificacao(classe, "alta", []),
        )

    todos_acesso = agregar_port_channels(
        [m("eth1/5", ClassePorta.ACESSO_SERVIDOR), m("eth1/6", ClassePorta.ACESSO_SERVIDOR)]
    )
    assert len(todos_acesso) == 1
    assert todos_acesso[0].cls.silenciar
    assert todos_acesso[0].porta.iface == "po22"

    com_desconhecida = agregar_port_channels(
        [m("eth1/5", ClassePorta.ACESSO_SERVIDOR), m("eth1/6", ClassePorta.DESCONHECIDA)]
    )
    assert not com_desconhecida[0].cls.silenciar

    infra = agregar_port_channels(
        [m("eth1/53", ClassePorta.UPLINK_FABRIC), m("eth1/54", ClassePorta.UPLINK_FABRIC)]
    )
    assert infra[0].cls.classe is ClassePorta.UPLINK_FABRIC
    assert not infra[0].cls.silenciar


def test_classificar_mapa_inclui_agregados():
    portas = [
        porta(iface="eth1/5", usage="epg", oper_st="up", bundle="po10"),
        porta(iface="eth1/6", usage="epg", oper_st="up", bundle="po10"),
    ]
    saida = classificar_mapa(portas, NOS)
    assert [m.porta.iface for m in saida] == ["eth1/5", "eth1/6", "po10"]

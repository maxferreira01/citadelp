"""CITADEL · ACI — coleta do mapa de portas de um fabric.

Sequência por fabric (tudo GET):
1. ``fabricNode`` (bulk, confiável) → leafs, spines e controllers.
2. Por leaf, em paralelo: ``sys.json?query-target=subtree&target-subtree-class=
   l1PhysIf,ethpmPhysIf`` (estado físico + config, 1 chamada traz as 2 classes)
   e ``sys/lldp/inst.json?...=lldpAdjEp`` (vizinhos; per-node por causa do bug
   do endpoint bulk — ver client.py).
3. ``fvRsPathAtt`` (bulk lógico, não sofre do bug de topology) → EPGs por porta,
   só nos paths diretos.
4. Join por chave pod/node/iface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from .client import AciClient
from .config import Fabric
from .modelos import (
    NoFabric,
    PortaFisica,
    VizinhoLLDP,
    chave_iface,
    parse_dn,
    parse_path_att,
)


@dataclass
class MapaColetado:
    """Resultado bruto da coleta, antes da classificação."""

    fabric_id: str
    nos: list[NoFabric] = field(default_factory=list)
    portas: list[PortaFisica] = field(default_factory=list)

    @property
    def leafs(self) -> list[NoFabric]:
        return [n for n in self.nos if n.role == "leaf"]

    @property
    def spines(self) -> list[NoFabric]:
        return [n for n in self.nos if n.role == "spine"]

    @property
    def controllers(self) -> list[NoFabric]:
        return [n for n in self.nos if n.role == "controller"]


def _attrs(obj: dict[str, Any], classe: str) -> dict[str, str] | None:
    item = obj.get(classe)
    if not item:
        return None
    return item.get("attributes", {})


def coletar_nos(client: AciClient) -> list[NoFabric]:
    nos: list[NoFabric] = []
    for obj in client.get_all_pages("/api/node/class/fabricNode.json"):
        a = _attrs(obj, "fabricNode")
        if a is None:
            continue
        pod, node_id, _ = parse_dn(a.get("dn", "") + "/")
        nos.append(
            NoFabric(
                pod=pod,
                node_id=node_id or a.get("id", ""),
                name=a.get("name", ""),
                role=a.get("role", ""),
                address=a.get("address", ""),
                model=a.get("model", ""),
                serial=a.get("serial", ""),
            )
        )
    return nos


def coletar_fabric(
    fabric: Fabric,
    transport: httpx.BaseTransport | None = None,
) -> MapaColetado:
    """Varre um fabric inteiro e devolve as portas físicas dos leafs, com join."""
    client = AciClient(fabric, transport=transport)
    try:
        nos = coletar_nos(client)
        leafs = [(n.pod, n.node_id) for n in nos if n.role == "leaf" and n.pod and n.node_id]
        nome_por_node = {n.node_id: n.name for n in nos}

        # --- estado físico + config (l1PhysIf + ethpmPhysIf na mesma chamada)
        fisico = client.por_no(
            leafs,
            lambda pod, node: (
                f"/api/node/mo/topology/pod-{pod}/node-{node}/sys.json"
                "?query-target=subtree&target-subtree-class=l1PhysIf,ethpmPhysIf"
            ),
        )
        portas: dict[str, PortaFisica] = {}
        ethpm: dict[str, dict[str, str]] = {}
        for lote in fisico:
            for obj in lote:
                a = _attrs(obj, "l1PhysIf")
                if a is not None:
                    pod, node_id, iface = parse_dn(a.get("dn", ""))
                    if not iface:
                        continue
                    portas[chave_iface(pod, node_id, iface)] = PortaFisica(
                        pod=pod,
                        node_id=node_id,
                        leaf_name=nome_por_node.get(node_id, ""),
                        iface=iface,
                        admin_st=a.get("adminSt", ""),
                        descr=a.get("descr", ""),
                        mode=a.get("mode", ""),
                        usage=a.get("usage", ""),
                    )
                    continue
                a = _attrs(obj, "ethpmPhysIf")
                if a is not None:
                    pod, node_id, iface = parse_dn(a.get("dn", ""))
                    if iface:
                        ethpm[chave_iface(pod, node_id, iface)] = a
        for chave, a in ethpm.items():
            p = portas.get(chave)
            if p is None:
                continue
            p.oper_st = a.get("operSt", "")
            p.oper_speed = a.get("operSpeed", "")
            p.oper_reason = a.get("operStQual", "")
            bundle = a.get("bundleIndex", "")
            p.bundle = "" if bundle in ("", "unspecified") else bundle
            p.last_link_chg = a.get("lastLinkStChg", "")

        # --- vizinhos LLDP (per-node; dedup por DN completo)
        lldp_lotes = client.por_no(
            leafs,
            lambda pod, node: (
                f"/api/node/mo/topology/pod-{pod}/node-{node}/sys/lldp/inst.json"
                "?query-target=subtree&target-subtree-class=lldpAdjEp"
            ),
        )
        vistos: set[str] = set()
        for lote in lldp_lotes:
            for obj in lote:
                a = _attrs(obj, "lldpAdjEp")
                if a is None:
                    continue
                dn = a.get("dn", "")
                if dn in vistos:
                    continue
                vistos.add(dn)
                pod, node_id, iface = parse_dn(dn)
                p = portas.get(chave_iface(pod, node_id, iface))
                if p is None:
                    continue
                p.lldp = VizinhoLLDP(
                    sys_name=a.get("sysName", ""),
                    sys_desc=a.get("sysDesc", ""),
                    mgmt_ip=a.get("mgmtIp", ""),
                    chassis_id=a.get("chassisIdV", ""),
                    port_id=a.get("portIdV", ""),
                    port_desc=a.get("portDesc", ""),
                    capability=a.get("capability", ""),
                )

        # --- binding EPG→porta (só paths diretos; VPC fica para usage/bundle)
        for obj in client.get_all_pages("/api/node/class/fvRsPathAtt.json"):
            a = _attrs(obj, "fvRsPathAtt")
            if a is None:
                continue
            att = parse_path_att(a.get("dn", ""), a.get("tDn", ""))
            if att is None:
                continue
            epg, pod, node_id, iface = att
            p = portas.get(chave_iface(pod, node_id, iface))
            if p is not None and epg not in p.epgs:
                p.epgs.append(epg)

        ordenadas = sorted(portas.values(), key=_ordem_porta)
        return MapaColetado(fabric_id=fabric.id, nos=nos, portas=ordenadas)
    finally:
        client.close()


def _ordem_porta(p: PortaFisica) -> tuple:
    """node numérico + slot/porta numéricos (eth1/9 antes de eth1/10)."""
    try:
        node = int(p.node_id)
    except ValueError:
        node = 0
    nums = [int(x) for x in re.findall(r"\d+", p.iface)]
    return (node, nums)

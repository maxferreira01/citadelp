"""CITADEL · ACI — regras de silenciamento de notificação no Checkmk.

Ruleset alvo: ``extra_service_conf:notifications_enabled`` com ``value_raw "'0'"``
(desabilita notificação do serviço; a COLETA continua — os gráficos de CRC das
portas de acesso no Grafana dependem disso).

Três pontos desenhados contra as pegadinhas conhecidas da REST API 2.x:

- A condição de service_description é REGEX DE PREFIXO: "Interface Ethernet1/1"
  casaria Ethernet1/10..19. Todo padrão gerado leva âncora ``$``.
- Uma regra aplica host_name × service_description em PRODUTO CARTESIANO.
  Por isso os leafs são agrupados por conjunto IDÊNTICO de portas a silenciar
  (pares VPC tendem a coincidir) e cada grupo vira UMA regra (g01, g02, ...).
- Idempotência por description: toda regra nossa começa com
  ``CITADEL aci-portmap <FABRIC>``; aplicar de novo REMOVE as antigas do fabric
  e cria as novas — substitui, nunca acumula.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..checkmk.gateway import CheckmkError, Gateway
from .modelos import ClassePorta

RULESET_NOTIF = "extra_service_conf:notifications_enabled"
PREFIXO_DESCRIPTION = "CITADEL aci-portmap"


def nome_servico(iface: str) -> str | None:
    """eth1/5 → "Interface Ethernet1/5"; po22 → "Interface port-channel22".

    O nome do serviço no Checkmk vem do ifDescr SNMP do NX-OS (Ethernet1/5,
    port-channel22) prefixado por "Interface ".
    """
    m = re.fullmatch(r"eth(\d+/\d+(?:/\d+)?)", iface)
    if m:
        return f"Interface Ethernet{m.group(1)}"
    m = re.fullmatch(r"po(\d+)", iface)
    if m:
        return f"Interface port-channel{m.group(1)}"
    return None


@dataclass
class RegraPlanejada:
    description: str
    hosts: list[str]
    servicos: list[str]  # padrões JÁ ancorados com $
    value_raw: str = "'0'"
    ruleset: str = RULESET_NOTIF

    def payload(self) -> dict:
        return {
            "ruleset": self.ruleset,
            "folder": "~",
            "value_raw": self.value_raw,
            "description": self.description,
            "conditions": {
                "host_name": {"match_on": self.hosts, "operator": "one_of"},
                "service_description": {"match_on": self.servicos, "operator": "one_of"},
            },
        }


@dataclass
class PlanoSite:
    fabric_id: str
    site_id: str
    regras: list[RegraPlanejada] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def total_servicos(self) -> int:
        return sum(len(r.hosts) * len(r.servicos) for r in self.regras)


def montar_plano(
    fabric_id: str,
    site_id: str,
    portas_por_leaf_cmk: dict[str, list[str]],
    data_ref: str,
) -> PlanoSite:
    """Agrupa leafs por conjunto idêntico de portas a silenciar → uma regra por grupo.

    ``portas_por_leaf_cmk``: host Checkmk → lista de ifaces ACI silenciáveis
    (só entram aqui portas com classe ACESSO_SERVIDOR/LIVRE e leafs já casados).
    """
    plano = PlanoSite(fabric_id=fabric_id, site_id=site_id)
    grupos: dict[tuple[str, ...], list[str]] = {}
    for host, ifaces in portas_por_leaf_cmk.items():
        servicos = sorted({s for i in ifaces if (s := nome_servico(i))})
        ignoradas = [i for i in ifaces if nome_servico(i) is None]
        if ignoradas:
            plano.avisos.append(f"{host}: ifaces sem serviço mapeável ignoradas: {ignoradas}")
        if servicos:
            grupos.setdefault(tuple(servicos), []).append(host)

    for n, (servicos, hosts) in enumerate(sorted(grupos.items(), key=lambda kv: kv[1]), start=1):
        plano.regras.append(
            RegraPlanejada(
                description=f"{PREFIXO_DESCRIPTION} {fabric_id} g{n:02d} {data_ref}",
                hosts=sorted(hosts),
                servicos=[s + "$" for s in servicos],
            )
        )
    return plano


def conferir_servicos_existem(gw: Gateway, plano: PlanoSite) -> list[str]:
    """Pré-apply: todo serviço planejado existe mesmo no host? (pega drift de
    nomenclatura por site/versão antes de criar regra morta). Read-only."""
    avisos: list[str] = []
    for regra in plano.regras:
        alvos = {s.rstrip("$") for s in regra.servicos}
        for host in regra.hosts:
            try:
                existentes = {
                    s.get("description", "")
                    for s in gw.list_services_monitorados(host, ["description"])
                }
            except CheckmkError as exc:
                avisos.append(f"{host}: não deu para listar serviços ({exc})")
                continue
            faltando = sorted(alvos - existentes)
            if faltando:
                avisos.append(
                    f"{host}: {len(faltando)} serviço(s) do plano não existem no core "
                    f"(ex.: {faltando[:3]}) — regra vale, mas não terá efeito neles"
                )
    return avisos


def aplicar_plano(gw: Gateway, plano: PlanoSite) -> dict:
    """Substitui as regras CITADEL do fabric no site: localiza → remove → cria →
    activate. Recibo verificado no padrão do restante do gateway."""
    recibo: dict = {"site": plano.site_id, "fabric": plano.fabric_id, "ok": False}
    marca = f"{PREFIXO_DESCRIPTION} {plano.fabric_id} "
    antigas = [
        r
        for r in gw.list_rules(RULESET_NOTIF)
        if r["properties"].get("description", "").startswith(marca)
    ]
    removidas = []
    for r in antigas:
        gw.delete_rule(r["id"])
        removidas.append(r["id"])
    criadas = []
    for regra in plano.regras:
        resp = gw.create_rule(
            ruleset=regra.ruleset,
            value_raw=regra.value_raw,
            conditions=regra.payload()["conditions"],
            description=regra.description,
            comment="gerada por scripts/aci_silenciar.py — não editar; regenerar pelo citadelp",
        )
        criadas.append(resp.get("id"))
        # topo da pasta: em ruleset first-match, regra genérica anterior
        # (ex.: '1' global sem condições) anularia o silenciamento inteiro
        if resp.get("id"):
            gw.move_rule(resp["id"])
    gw.activate(force_foreign=False)
    recibo.update({"ok": True, "removidas": removidas, "criadas": criadas})
    return recibo


def verificar_plano(gw: Gateway, plano: PlanoSite, mantem_alarme: dict[str, list[str]]) -> dict:
    """Pós-apply, os DOIS lados: alvo do plano com notificação desligada E
    uplink/infra com notificação ligada (pega regra que não pegou e regra que
    pegou demais). ``mantem_alarme``: host → serviços que DEVEM continuar com
    notificação (uplinks etc.)."""
    silenciados_errado: list[str] = []
    alarmando_errado: list[str] = []
    for regra in plano.regras:
        alvos = {s.rstrip("$") for s in regra.servicos}
        for host in regra.hosts:
            estado = {
                s.get("description", ""): s.get("notifications_enabled")
                for s in gw.list_services_monitorados(
                    host, ["description", "notifications_enabled"]
                )
            }
            for svc in sorted(alvos):
                if svc in estado and estado[svc] not in (0, "0"):
                    alarmando_errado.append(f"{host} / {svc}")
            for svc in mantem_alarme.get(host, []):
                if svc in estado and estado[svc] in (0, "0"):
                    silenciados_errado.append(f"{host} / {svc}")
    return {
        "ok": not silenciados_errado and not alarmando_errado,
        "alvo_ainda_notificando": alarmando_errado,
        "infra_silenciada_indevidamente": silenciados_errado,
    }


CLASSES_MANTEM_ALARME = frozenset(
    {
        ClassePorta.UPLINK_FABRIC,
        ClassePorta.UPLINK_APIC,
        ClassePorta.FIREWALL,
        ClassePorta.ROTEADOR,
        ClassePorta.NSX_EDGE,
        ClassePorta.SW_GERENCIA,
        ClassePorta.DESCONHECIDA,
    }
)

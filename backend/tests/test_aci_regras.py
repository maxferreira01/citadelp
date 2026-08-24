"""Regras de silenciamento — payload, âncoras, agrupamento e idempotência."""

from __future__ import annotations

import json

import httpx

from app.aci.regras import (
    RULESET_NOTIF,
    aplicar_plano,
    montar_plano,
    nome_servico,
    verificar_plano,
)
from app.checkmk.gateway import Gateway, Site

SITE = Site(id="tesp6", url="https://cmk.local/tesp6", user="u", secret="s")


def test_nome_servico():
    assert nome_servico("eth1/5") == "Interface Ethernet1/5"
    assert nome_servico("eth1/1/2") == "Interface Ethernet1/1/2"
    assert nome_servico("po22") == "Interface port-channel22"
    assert nome_servico("mgmt0") is None


def test_todo_padrao_leva_ancora_por_causa_do_prefixo_regex_do_cmk():
    plano = montar_plano("TESP6", "tesp6", {"LEAF1001TESP6": ["eth1/1", "po22"]}, "20260824")
    servicos = plano.regras[0].servicos
    assert servicos == ["Interface Ethernet1/1$", "Interface port-channel22$"]
    # sem a âncora, "Interface Ethernet1/1" casaria Ethernet1/10..19


def test_agrupamento_por_conjunto_identico_de_portas():
    plano = montar_plano(
        "TESP6",
        "tesp6",
        {
            "LEAF1001TESP6": ["eth1/1", "eth1/2"],  # par VPC: mesmo conjunto
            "LEAF1002TESP6": ["eth1/2", "eth1/1"],
            "LEAF1003TESP6": ["eth1/9"],  # conjunto diferente → outra regra
        },
        "20260824",
    )
    assert len(plano.regras) == 2
    grupos = {tuple(r.hosts): r.servicos for r in plano.regras}
    assert grupos[("LEAF1001TESP6", "LEAF1002TESP6")] == [
        "Interface Ethernet1/1$",
        "Interface Ethernet1/2$",
    ]
    assert grupos[("LEAF1003TESP6",)] == ["Interface Ethernet1/9$"]
    assert all(r.value_raw == "'0'" for r in plano.regras)
    assert all(r.description.startswith("CITADEL aci-portmap TESP6 g") for r in plano.regras)


def test_aplicar_e_idempotente_remove_antigas_cria_novas_e_ativa():
    eventos: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        path = req.url.path
        if req.method == "GET" and path.endswith("/domain-types/rule/collections/all"):
            eventos.append("list")
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "id": "velha-1",
                            "extensions": {
                                "ruleset": RULESET_NOTIF,
                                "properties": {
                                    "description": "CITADEL aci-portmap TESP6 g01 20260101"
                                },
                            },
                        },
                        {
                            "id": "de-outro-fabric",
                            "extensions": {
                                "ruleset": RULESET_NOTIF,
                                "properties": {
                                    "description": "CITADEL aci-portmap TESP03 g01 20260101"
                                },
                            },
                        },
                    ]
                },
            )
        if req.method == "DELETE":
            eventos.append(f"delete:{path.rsplit('/', 1)[-1]}")
            assert req.headers["If-Match"] == "*"
            return httpx.Response(204)
        if req.method == "POST" and path.endswith("/domain-types/rule/collections/all"):
            corpo = json.loads(req.content)
            eventos.append("create")
            assert corpo["ruleset"] == RULESET_NOTIF
            assert corpo["folder"] == "~"
            assert corpo["value_raw"] == "'0'"
            assert corpo["conditions"]["service_description"]["match_on"] == [
                "Interface Ethernet1/1$"
            ]
            return httpx.Response(200, json={"id": "nova-1"})
        if req.method == "POST" and "/actions/move/invoke" in path:
            corpo = json.loads(req.content)
            eventos.append(f"move:{path.split('/')[-4]}")
            assert corpo == {"position": "top_of_folder", "folder": "~"}
            return httpx.Response(200, json={})
        if "activate-changes" in path:
            eventos.append("activate")
            return httpx.Response(200, json={})
        raise AssertionError(f"chamada inesperada: {req.method} {path}")

    plano = montar_plano("TESP6", "tesp6", {"LEAF1001TESP6": ["eth1/1"]}, "20260824")
    gw = Gateway(SITE, transport=httpx.MockTransport(handler))
    recibo = aplicar_plano(gw, plano)
    # remove SÓ as antigas do mesmo fabric, cria, move ao TOPO (regra genérica
    # anterior não pode anular o silenciamento), ativa — nessa ordem
    assert eventos == ["list", "delete:velha-1", "create", "move:nova-1", "activate"]
    assert recibo["ok"] and recibo["removidas"] == ["velha-1"] and recibo["criadas"] == ["nova-1"]


def test_verificacao_pega_os_dois_lados():
    def handler(req: httpx.Request) -> httpx.Response:
        assert "/collections/services" in req.url.path
        return httpx.Response(
            200,
            json={
                "value": [
                    # alvo do plano ainda notificando (regra não pegou)
                    {
                        "extensions": {
                            "description": "Interface Ethernet1/1",
                            "notifications_enabled": 1,
                        }
                    },
                    # uplink silenciado indevidamente (regra pegou demais)
                    {
                        "extensions": {
                            "description": "Interface Ethernet1/53",
                            "notifications_enabled": 0,
                        }
                    },
                ]
            },
        )

    plano = montar_plano("TESP6", "tesp6", {"LEAF1001TESP6": ["eth1/1"]}, "20260824")
    gw = Gateway(SITE, transport=httpx.MockTransport(handler))
    resultado = verificar_plano(gw, plano, {"LEAF1001TESP6": ["Interface Ethernet1/53"]})
    assert not resultado["ok"]
    assert resultado["alvo_ainda_notificando"] == ["LEAF1001TESP6 / Interface Ethernet1/1"]
    assert resultado["infra_silenciada_indevidamente"] == ["LEAF1001TESP6 / Interface Ethernet1/53"]

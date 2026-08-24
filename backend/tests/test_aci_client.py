"""Cliente APIC — login/cookie, paginação e a regra de ouro: LLDP per-node."""

from __future__ import annotations

import json

import httpx
import pytest

from app.aci.client import AciClient, AciError
from app.aci.coleta import coletar_fabric
from app.aci.config import Fabric

FABRIC = Fabric(id="TESTE", apic_url="https://apic.local", user="u", secret="s")


def resposta_login(token="tok-1", refresh="600"):
    return {
        "imdata": [{"aaaLogin": {"attributes": {"token": token, "refreshTimeoutSeconds": refresh}}}]
    }


def imdata(*objs, total=None):
    return {"totalCount": str(total if total is not None else len(objs)), "imdata": list(objs)}


def test_login_e_cookie_nas_requisicoes_seguintes():
    chamadas: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        chamadas.append(req)
        if req.url.path == "/api/aaaLogin.json":
            corpo = json.loads(req.content)
            assert corpo["aaaUser"]["attributes"] == {"name": "u", "pwd": "s"}
            return httpx.Response(200, json=resposta_login())
        assert req.headers["Cookie"] == "APIC-cookie=tok-1"
        return httpx.Response(200, json=imdata())

    c = AciClient(FABRIC, transport=httpx.MockTransport(handler))
    assert c.get_all_pages("/api/node/class/fabricNode.json") == []
    assert chamadas[0].url.path == "/api/aaaLogin.json"


def test_login_401_falha_sem_insistir():
    tentativas = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        tentativas["n"] += 1
        return httpx.Response(401, json={})

    c = AciClient(FABRIC, transport=httpx.MockTransport(handler))
    with pytest.raises(AciError) as exc:
        c.get("/api/node/class/fabricNode.json")
    assert exc.value.status == 401
    assert tentativas["n"] == 1  # credencial errada repetida é o que trava conta


def test_paginacao_acumula_ate_totalcount():
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/api/aaaLogin.json":
            return httpx.Response(200, json=resposta_login())
        page = req.url.params["page"]
        objs = {"0": [{"x": 1}, {"x": 2}], "1": [{"x": 3}]}[page]
        return httpx.Response(200, json={"totalCount": "3", "imdata": objs})

    c = AciClient(FABRIC, transport=httpx.MockTransport(handler))
    assert len(c.get_all_pages("/api/node/class/coisa.json")) == 3


def test_coleta_lldp_e_sempre_per_node_nunca_bulk():
    """O endpoint bulk de lldpAdjEp duplica páginas e OMITE nós inteiros —
    qualquer regressão para ele quebra o mapa em silêncio."""
    paths: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        paths.append(req.url.path)
        if req.url.path == "/api/aaaLogin.json":
            return httpx.Response(200, json=resposta_login())
        if req.url.path == "/api/node/class/fabricNode.json":
            return httpx.Response(
                200,
                json=imdata(
                    {
                        "fabricNode": {
                            "attributes": {
                                "dn": "topology/pod-1/node-1001/sys",
                                "name": "LEAF1001",
                                "role": "leaf",
                                "address": "10.0.0.2",
                            }
                        }
                    }
                ),
            )
        return httpx.Response(200, json=imdata())

    coletar_fabric(FABRIC, transport=httpx.MockTransport(handler))
    assert "/api/node/class/lldpAdjEp.json" not in paths
    assert "/api/node/mo/topology/pod-1/node-1001/sys/lldp/inst.json" in paths
    assert "/api/node/mo/topology/pod-1/node-1001/sys.json" in paths


def test_erro_em_um_no_derruba_o_fabric():
    """Mapa parcial silenciosamente incompleto é pior que falha explícita."""

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/api/aaaLogin.json":
            return httpx.Response(200, json=resposta_login())
        if req.url.path == "/api/node/class/fabricNode.json":
            return httpx.Response(
                200,
                json=imdata(
                    {
                        "fabricNode": {
                            "attributes": {
                                "dn": "topology/pod-1/node-1001/sys",
                                "name": "LEAF1001",
                                "role": "leaf",
                            }
                        }
                    }
                ),
            )
        if "node-1001/sys.json" in req.url.path:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json=imdata())

    with pytest.raises(AciError):
        coletar_fabric(FABRIC, transport=httpx.MockTransport(handler))

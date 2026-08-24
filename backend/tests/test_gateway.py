import json

import httpx

from app.checkmk.gateway import (
    Gateway,
    Site,
    listar_downtimes,
    load_sites,
    normalizar_downtime,
    rdm_downtime,
    remover_downtimes,
)

SITE = Site(id="tesp03", url="https://cmk.local/tesp03", user="citadel_api", secret="s3cr3t")


def transport(recorder):
    def handler(req: httpx.Request) -> httpx.Response:
        recorder.append(req)
        return httpx.Response(200, json={"ok": True, "value": []})

    return httpx.MockTransport(handler)


def test_headers_e_base_url():
    assert SITE.base == "https://cmk.local/tesp03/check_mk/api/1.0"
    assert SITE.headers["Authorization"] == "Bearer citadel_api s3cr3t"


def test_create_host_payload():
    reqs = []
    gw = Gateway(SITE, transport=transport(reqs))
    gw.create_host("edge-fw01", folder="/redes", ipaddress="10.30.3.5")
    body = json.loads(reqs[0].content)
    assert reqs[0].url.path.endswith("/domain-types/host_config/collections/all")
    assert body == {
        "folder": "/redes",
        "host_name": "edge-fw01",
        "attributes": {"ipaddress": "10.30.3.5"},
    }


def test_downtime_de_servico():
    reqs = []
    gw = Gateway(SITE, transport=transport(reqs))
    gw.schedule_downtime("edge-fw01", 60, "RDM 549523", services=["Float IP"])
    body = json.loads(reqs[0].content)
    assert reqs[0].url.path.endswith("/domain-types/downtime/collections/service")
    assert body["downtime_type"] == "service"
    assert body["service_descriptions"] == ["Float IP"]
    assert "RDM 549523" in body["comment"]


def test_activate_envia_if_match():
    reqs = []
    Gateway(SITE, transport=transport(reqs)).activate()
    assert reqs[0].headers["If-Match"] == "*"


def test_rdm_downtime_nao_para_no_erro():
    sites = {"tesp03": SITE}
    plan = [
        {"site": "tesp03", "host": "edge-fw01", "services": None},
        {"site": "inexistente", "host": "x", "services": None},
    ]
    reqs = []
    receipts = rdm_downtime(sites, plan, rdm="549523", minutes=120, transport=transport(reqs))
    assert receipts[0]["ok"] is True
    assert receipts[1]["ok"] is False and "não registrado" in receipts[1]["error"]


def test_list_hosts_reenvia_sem_include_links_em_site_21():
    # Sites 2.1 respondem 400 "Unknown field" ao include_links; o gateway
    # deve repetir a listagem sem o parâmetro em vez de propagar o erro.
    reqs = []

    def handler(req: httpx.Request) -> httpx.Response:
        reqs.append(req)
        if "include_links" in str(req.url):
            return httpx.Response(
                400,
                json={"fields": {"include_links": ["Unknown field."]}},
            )
        return httpx.Response(
            200,
            json={"value": [{"id": "LEAF1001TESP2", "extensions": {"folder": "/redes"}}]},
        )

    gw = Gateway(SITE, transport=httpx.MockTransport(handler))
    hosts = gw.list_hosts()
    assert len(reqs) == 2 and "include_links" not in str(reqs[1].url)
    assert hosts == [{"id": "LEAF1001TESP2", "folder": "/redes"}]


def test_load_sites_do_json():
    sites = load_sites('[{"id":"a","url":"https://x/a","user":"u","secret":"p"}]')
    assert sites["a"].user == "u"


def _downtime(did: str, host: str, servico: str | None = None) -> dict:
    return {
        "id": did,
        "title": (f"Downtime for service: {servico}" if servico else f"Downtime for host: {host}"),
        "extensions": {
            "host_name": host,
            "author": "citadel_api",
            "is_service": "yes" if servico else "no",
            "start_time": "2026-07-28T10:00:00",
            "end_time": "2026-07-28T12:00:00",
            "recurring": "no",
            "comment": "RDM 1",
        },
    }


def test_normalizar_extrai_servico_do_title():
    item = normalizar_downtime("tesp3", _downtime("7", "fw01", "CPU utilization"))
    assert item["servico"] == "CPU utilization"
    assert item["tipo"] == "service" and item["host"] == "fw01" and item["site"] == "tesp3"
    host = normalizar_downtime("tesp3", _downtime("8", "fw01"))
    assert host["servico"] is None and host["tipo"] == "host"


def test_list_downtimes_monta_filtro_livestatus():
    reqs = []

    def handler(req):
        reqs.append(req)
        return httpx.Response(200, json={"value": []})

    gw = Gateway(SITE, transport=httpx.MockTransport(handler))
    gw.list_downtimes(host_name="fw01", tipo="service")
    q = json.loads(dict(reqs[0].url.params)["query"])
    assert q["op"] == "and"
    assert {"op": "=", "left": "downtimes.host_name", "right": "fw01"} in q["expr"]
    assert {"op": "=", "left": "downtimes.is_service", "right": "1"} in q["expr"]


def test_listar_downtimes_isola_erro_de_site():
    def handler(req):
        if "quebrado" in str(req.url):
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json={"value": [_downtime("1", "fw01", "CPU")]})

    sites = {
        "ok": SITE,
        "quebrado": Site(id="quebrado", url="https://quebrado/x", user="u", secret="s"),
    }
    r = listar_downtimes(sites, transport=httpx.MockTransport(handler))
    assert r["total"] == 1 and r["itens"][0]["servico"] == "CPU"
    assert r["erros"][0]["site"] == "quebrado"


def _handler_por_host(chamadas, estado):
    """by_id não resolve; só a remoção por host limpa (caso do site federado)."""

    def handler(req):
        if req.method == "GET":
            itens = [_downtime("9", "fw01", "CPU"), _downtime("10", "fw01", "Memory")]
            return httpx.Response(200, json={"value": itens if estado["presente"] else []})
        body = json.loads(req.content)
        chamadas.append(body)
        if body["delete_type"] == "params" and "service_descriptions" not in body:
            estado["presente"] = False
        return httpx.Response(204)

    return httpx.MockTransport(handler)


def test_remover_exige_confirmacao_antes_de_apagar_por_host():
    chamadas, estado = [], {"presente": True}
    recibos = remover_downtimes(
        {"tesp3": SITE},
        [{"site": "tesp3", "id": "9", "host": "fw01", "servico": "CPU"}],
        transport=_handler_por_host(chamadas, estado),
        espera=0,
    )
    assert [c["delete_type"] for c in chamadas] == ["by_id"]  # não apagou por host
    assert recibos[0]["ok"] is False
    assert recibos[0]["requer_confirmacao"] is True
    assert recibos[0]["colaterais"] == 1  # o downtime "10" seria levado junto


def test_remover_por_host_quando_confirmado():
    chamadas, estado = [], {"presente": True}
    recibos = remover_downtimes(
        {"tesp3": SITE},
        [{"site": "tesp3", "id": "9", "host": "fw01", "servico": "CPU"}],
        transport=_handler_por_host(chamadas, estado),
        espera=0,
        forcar_por_host=True,
    )
    assert [c["delete_type"] for c in chamadas] == ["by_id", "params"]
    assert "service_descriptions" not in chamadas[1]  # o filtro de serviço não funciona
    assert recibos[0]["ok"] is True and recibos[0]["via"] == "por_host"
    assert recibos[0]["colaterais"] == ["10"]


def test_remover_reporta_falha_quando_downtime_sobrevive():
    def handler(req):
        if req.method == "GET":
            return httpx.Response(200, json={"value": [_downtime("9", "fw01", "CPU")]})
        return httpx.Response(204)  # mente: 204 mas nada é removido

    recibos = remover_downtimes(
        {"tesp3": SITE},
        [{"site": "tesp3", "id": "9", "host": "fw01", "servico": "CPU"}],
        transport=httpx.MockTransport(handler),
        espera=0,
        forcar_por_host=True,
    )
    assert recibos[0]["ok"] is False and "não removido" in recibos[0]["erro"]


def test_remover_site_desconhecido():
    recibos = remover_downtimes({}, [{"site": "x", "id": "1"}])
    assert recibos[0]["ok"] is False and "não registrado" in recibos[0]["erro"]

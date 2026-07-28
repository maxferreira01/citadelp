import json

import httpx

from app.checkmk.gateway import Gateway, Site, load_sites, rdm_downtime

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


def test_load_sites_do_json():
    sites = load_sites('[{"id":"a","url":"https://x/a","user":"u","secret":"p"}]')
    assert sites["a"].user == "u"

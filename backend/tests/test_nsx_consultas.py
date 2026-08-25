"""Read-model NSX — parse do CSV anotado, aliases de site e pivot das consultas."""

from __future__ import annotations

import httpx
import pytest

from app.nsx.client import InfluxClient, NsxError, parse_csv_anotado
from app.nsx.config import Aliases, InfluxConfig, NsxConfigError, load_aliases, load_influx
from app.nsx.consultas import Consultas, flux_per_t0

CFG = InfluxConfig(url="http://influx.local:8086", org="TOTVS", token="t")
ALIASES = Aliases({"TESP06": "TESP6", "TESP07": "TESP7"})

CSV_TOTALS = (
    "#group,false,false,true,true,false,false,false\r\n"
    "#datatype,string,long,string,dateTime:RFC3339,double,double,double\r\n"
    "#default,_result,,,,,,\r\n"
    ",result,table,site,_time,on_t0,on_vrf,total\r\n"
    ",_result,0,TESP6,2026-08-25T18:38:12Z,635,1207,1842\r\n"
    ",_result,1,TESP06,2026-06-12T00:00:00Z,600,1200,1800\r\n"
    "\r\n"
)
CSV_CAP = (
    "#group,false,false,true,true,false,false,false\r\n"
    "#datatype,string,long,string,dateTime:RFC3339,double,double,double\r\n"
    "#default,_result,,,,,,\r\n"
    ",result,table,site,_time,current_usage,max_supported,usage_pct\r\n"
    ",_result,0,TESP6,2026-08-25T18:38:12Z,1842,4000,46.05\r\n"
    "\r\n"
)
CSV_T0 = (
    "#group,false,false,true,true,true,true,false,false,false,false\r\n"
    "#datatype,string,long,string,string,string,dateTime:RFC3339,double,double,double,double\r\n"
    "#default,_result,,,,,,,,,\r\n"
    ",result,table,site,t0_name,t0_id,_time,available,limit,t1_count,usage_pct\r\n"
    ",_result,0,TESP6,T0-Cluster_1,c888,2026-08-25T18:38:12Z,797,1000,203,20.3\r\n"
    ",_result,0,TESP6,T0-Cluster_4,b4ea,2026-08-25T18:38:12Z,966,1000,34,3.4000000000000004\r\n"
    "\r\n"
)


def test_parse_csv_anotado_tipa_e_ignora_colunas_internas():
    linhas = parse_csv_anotado(CSV_TOTALS)
    assert linhas[0] == {
        "site": "TESP6",
        "_time": "2026-08-25T18:38:12Z",
        "on_t0": 635.0,
        "on_vrf": 1207.0,
        "total": 1842.0,
    }
    assert "result" not in linhas[0] and "table" not in linhas[0]


def test_parse_csv_varias_tabelas_com_cabecalhos_diferentes():
    linhas = parse_csv_anotado(CSV_TOTALS + CSV_CAP)
    assert len(linhas) == 3
    assert linhas[2]["max_supported"] == 4000.0


def test_aliases_canonico_variantes_e_regex_escapado():
    assert ALIASES.canonico("TESP06") == "TESP6"
    assert ALIASES.variantes("TESP6") == ["TESP6", "TESP06"]
    assert ALIASES.regex("TESP6") == "^(TESP6|TESP06)$"
    # site sem alias casa só ele mesmo; metacaracteres nunca vão crus ao Flux
    assert Aliases().regex("TESP7-INFRA.BASE") == r"^(TESP7\-INFRA\.BASE)$"
    assert "TESP6|TESP06" in flux_per_t0("nsx_capacity", ALIASES, "TESP06")


def _client(handler) -> InfluxClient:
    return InfluxClient(CFG, transport=httpx.MockTransport(handler))


def test_resumo_junta_totals_e_capacity_normalizando_site():
    chamadas: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/api/v2/query" and req.url.params["org"] == "TOTVS"
        assert req.headers["Authorization"] == "Token t"
        flux = req.read().decode()
        chamadas.append(flux)
        if "nsx_t1_totals" in flux:
            return httpx.Response(200, text=CSV_TOTALS)
        return httpx.Response(200, text=CSV_CAP)

    q = Consultas(_client(handler), ALIASES)
    out = q.resumo()
    assert len(out) == 1  # TESP06 e TESP6 viram uma linha só
    r = out[0]
    assert r.site == "TESP6" and r.variantes == ["TESP06", "TESP6"]
    assert (r.total, r.on_vrf, r.on_t0) == (1842, 1207, 635)
    assert (r.nsx_current, r.nsx_max, r.nsx_pct) == (1842, 4000, 46.05)
    assert "bucket: \\\"nsx\\\"" in chamadas[0] and "nsx_capacity" in chamadas[1]  # totals no bucket default


def test_por_t0_converte_tipos_do_pivot():
    q = Consultas(_client(lambda req: httpx.Response(200, text=CSV_T0)), ALIASES)
    linhas = q.por_t0("TESP6")
    assert [t.t0_name for t in linhas] == ["T0-Cluster_1", "T0-Cluster_4"]
    assert linhas[1].t1_count == 34 and linhas[1].usage_pct == 3.4 and linhas[1].limit == 1000
    assert linhas[0].atualizado_em == "2026-08-25T18:38:12Z"


def test_influx_401_vira_nsxerror_com_status():
    q = Consultas(_client(lambda req: httpx.Response(401, text="unauthorized")), ALIASES)
    with pytest.raises(NsxError) as exc:
        q.resumo()
    assert exc.value.status == 401


def test_config_exige_token_e_json_valido():
    with pytest.raises(NsxConfigError):
        load_influx('{"url":"http://x","org":"o"}', token="")
    with pytest.raises(NsxConfigError):
        load_influx("{nao-json", token="t")
    cfg = load_influx('{"url":"http://x/","org":"o","bucket_capacity":"cap"}', token="t")
    assert cfg.base == "http://x" and cfg.bucket_nsx == "nsx" and cfg.bucket_capacity == "cap"
    assert load_aliases('{"TESP06":"TESP6"}').canonico("TESP06") == "TESP6"

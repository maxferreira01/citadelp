"""Matching leaf ACI ↔ host Checkmk — as inconsistências reais do parque."""

from __future__ import annotations

from app.aci.cmk_match import SiteDescoberto, casar_leafs, normalizar_leaf


def descobertos(**hosts_por_site: list[str]) -> dict[str, SiteDescoberto]:
    return {
        sid: SiteDescoberto(site_id=sid, versao="2.1.0p20", hosts_leaf=hosts)
        for sid, hosts in hosts_por_site.items()
    }


def test_normalizacao_de_zeros_dos_dois_lados():
    assert normalizar_leaf("LEAF1017TESP07") == ("1017", "TESP7")
    assert normalizar_leaf("LEAF1001TESP03") == ("1001", "TESP3")
    assert normalizar_leaf("LEAF1001TBSP2") == ("1001", "TBSP2")
    assert normalizar_leaf("FW01TESP6") is None


def test_match_exato_e_normalizado():
    d = descobertos(tesp7=["LEAF1001TESP7", "LEAF1017TESP7"])
    ms = {m.leaf_aci: m for m in casar_leafs(["LEAF1001TESP7", "LEAF1017TESP07"], d, "tesp7")}
    assert ms["LEAF1001TESP7"].camada == "exato"
    # LEAF1017TESP07 (zero a mais no ACI) casa com LEAF1017TESP7 do CMK
    assert ms["LEAF1017TESP07"].host_cmk == "LEAF1017TESP7"
    assert ms["LEAF1017TESP07"].camada == "normalizado"
    assert ms["LEAF1017TESP07"].confianca == "alta"


def test_leaf_tbsp2_dentro_do_fabric_tesp2_casa_por_numero_unico():
    d = descobertos(tesp2=["LEAF1003TESP2", "LEAF1001TBSP2"])
    ms = {m.leaf_aci: m for m in casar_leafs(["LEAF1001TBSP2"], d, "tesp2")}
    m = ms["LEAF1001TBSP2"]
    assert m.camada == "exato"  # nome bate literalmente, mesmo sendo "TBSP2" no site tesp2
    # leaf renomeado no CMK (TESP2) mas número único no site → camada 3
    d2 = descobertos(tesp2=["LEAF1003TESP2", "LEAF1001TESP2"])
    m2 = casar_leafs(["LEAF1001TBSP2"], d2, "tesp2")[0]
    assert m2.camada == "numero-unico"
    assert m2.confianca == "media"  # média nunca entra em regra


def test_ambiguo_e_ausente_ficam_sem_match():
    # dois hosts com o mesmo número de leaf no site → não dá para decidir
    d = descobertos(tesp2=["LEAF1001TESP2", "LEAF1001TBSP2"])
    ambiguo = casar_leafs(["LEAF1001TBCE9"], d, "tesp2")[0]
    assert ambiguo.camada == "sem-match"
    assert ambiguo.host_cmk is None
    ausente = casar_leafs(["LEAF2044TESP2"], d, "tesp2")[0]
    assert ausente.camada == "sem-match"


def test_colisao_host_em_dois_sites_e_sinalizada():
    # cenário mk_tece1/mk_tesp2: mesmo endpoint respondendo pelos dois "sites"
    d = descobertos(tesp2=["LEAF1001TESP2"], tece1=["LEAF1001TESP2"])
    m = casar_leafs(["LEAF1001TESP2"], d, "tesp2")[0]
    assert m.camada == "exato"
    assert "COLISÃO" in m.detalhe
    assert "tece1" in m.detalhe

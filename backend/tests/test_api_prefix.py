"""/api/<rota> é sinônimo de /<rota> (a SPA usa o prefixo; externos usam a raiz)."""

from fastapi.testclient import TestClient

from app.main import app


def test_api_prefix_equivale_a_raiz():
    c = TestClient(app)
    assert c.get("/healthz").json()["ok"] is True
    assert c.get("/api/healthz").json() == c.get("/healthz").json()


def test_api_prefix_so_reescreve_o_prefixo_exato():
    c = TestClient(app)
    # "/apiario" não é "/api/…": não pode virar "/ario"
    assert c.get("/apiario").status_code == 404

"""Manager NSX (GET only) — result_count, capacity, paginação e edge clusters."""

from __future__ import annotations

import httpx
import pytest

from app.nsx.config import Manager
from app.nsx.manager import ManagerClient, ManagerError

MGR = Manager(id="TESP6", url="https://mgr.local", user_env="U_T", password_env="P_T")


@pytest.fixture(autouse=True)
def _cred(monkeypatch):
    monkeypatch.setenv("U_T", "u")
    monkeypatch.setenv("P_T", "p")


def test_total_capacity_e_edge_clusters():
    metodos: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        metodos.append(req.method)
        p = req.url.path
        if p == "/policy/api/v1/infra/tier-1s":
            assert req.url.params["page_size"] == "1"
            return httpx.Response(200, json={"result_count": 1842, "results": [{}]})
        if p == "/api/v1/capacity/usage":
            return httpx.Response(
                200,
                json={
                    "capacity_usage": [
                        {
                            "usage_type": "NUMBER_OF_TIER1_ROUTERS",
                            "current_usage_count": 1842,
                            "max_supported_count": 4000,
                            "current_usage_percentage": 46.05,
                            "severity": "INFO",
                        }
                    ]
                },
            )
        if p.endswith("/edge-clusters"):
            return httpx.Response(
                200, json={"results": [{"id": "ec1", "display_name": "EC-Cluster_1"}]}
            )
        if p == "/api/v1/logical-routers":
            if "cursor" not in req.url.params:
                return httpx.Response(
                    200,
                    json={
                        "cursor": "c2",
                        "results": [
                            {"router_type": "TIER1", "edge_cluster_id": "ec1"},
                            {"router_type": "TIER0", "edge_cluster_id": "ec1"},
                        ],
                    },
                )
            return httpx.Response(
                200,
                json={
                    "results": [
                        {"router_type": "TIER1", "edge_cluster_id": "ec1"},
                        {"router_type": "TIER1"},
                    ]
                },
            )
        return httpx.Response(404)

    c = ManagerClient(MGR, transport=httpx.MockTransport(handler))
    assert c.total_tier1() == 1842
    assert c.capacity_tier1()["max"] == 4000
    edges = c.por_edge_cluster()
    assert [(e.edge_cluster_name, e.t1_count) for e in edges] == [
        ("EC-Cluster_1", 2),
        ("(sem edge cluster)", 1),
    ]
    assert set(metodos) == {"GET"}  # nunca outra coisa


def test_403_nao_insiste():
    n = {"v": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        n["v"] += 1
        return httpx.Response(403, json={"error_message": "locked"})

    c = ManagerClient(MGR, transport=httpx.MockTransport(handler))
    with pytest.raises(ManagerError) as exc:
        c.total_tier1()
    assert exc.value.status == 403 and n["v"] == 1

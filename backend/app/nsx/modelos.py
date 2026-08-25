"""CITADEL · NSX — modelos do read-model de capacity de T1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ResumoSite:
    """Uma linha por site: totals do collector + capacity dashboard do NSX.

    ``total``/``on_vrf``/``on_t0`` vêm de ``nsx_t1_totals`` (contagem própria
    do collector); ``nsx_current``/``nsx_max`` vêm de ``nsx_capacity``
    (``NUMBER_OF_TIER1_ROUTERS``, o que a Manager reporta em /capacity/usage).
    Divergência entre os dois é sinal, não ruído.
    """

    site: str
    total: int | None = None
    on_vrf: int | None = None
    on_t0: int | None = None
    nsx_current: int | None = None
    nsx_max: int | None = None
    nsx_pct: float | None = None
    atualizado_em: str | None = None
    variantes: list[str] = field(default_factory=list)

    def dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T1PorT0:
    site: str
    t0_name: str
    t0_id: str = ""
    t1_count: int = 0
    limit: int = 0
    usage_pct: float = 0.0
    available: int = 0
    atualizado_em: str | None = None

    def dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T1PorVrf:
    site: str
    vrf_name: str
    vrf_id: str = ""
    t0_parent: str = ""
    t1_count: int = 0
    limit: int = 0
    usage_pct: float = 0.0
    available: int = 0
    atualizado_em: str | None = None

    def dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T1PorEdge:
    """T1 por edge cluster — hoje só via Manager (CLI --com-edge); vira série
    quando o collector persistir ``nsx_t1_per_edge_cluster`` (proposta)."""

    site: str
    edge_cluster_name: str
    edge_cluster_id: str = ""
    t1_count: int = 0

    def dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EventoT1:
    site: str
    quando: str
    event: str  # created | deleted
    t1_name: str
    t1_id: str = ""
    # nome do PARENT (VRF ou T0) — o collector chama de vrf_name mesmo quando é T0
    parent_name: str = ""
    edge_cluster_name: str = ""
    site_t1_total: int | None = None

    def dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PontoHistorico:
    quando: str
    total: int | None

    def dict(self) -> dict:
        return asdict(self)

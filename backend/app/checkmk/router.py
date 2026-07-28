"""Endpoints REST do gateway Checkmk (consumidos pelo painel CORVO)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.checkmk.gateway import CheckmkError, Gateway, load_sites, rdm_downtime

router = APIRouter(prefix="/checkmk", tags=["Corvo · Checkmk"])


class HostIn(BaseModel):
    host_name: str
    folder: str = "/"
    ipaddress: str | None = None
    labels: dict[str, str] | None = None
    discover: bool = True
    activate: bool = True


class DowntimeIn(BaseModel):
    host_name: str
    minutes: int = Field(gt=0, le=7 * 24 * 60)
    comment: str
    services: list[str] | None = None


class RdmPlanItem(BaseModel):
    site: str
    host: str
    services: list[str] | None = None


class RdmIn(BaseModel):
    rdm: str
    minutes: int = Field(gt=0, le=7 * 24 * 60)
    plan: list[RdmPlanItem]


def _gw(site_id: str) -> Gateway:
    sites = load_sites()
    if site_id not in sites:
        raise HTTPException(404, f"site '{site_id}' não registrado")
    return Gateway(sites[site_id])


@router.get("/sites")
def list_sites() -> list[dict]:
    return [{"id": s.id, "url": s.url} for s in load_sites().values()]


@router.post("/{site_id}/hosts", status_code=201)
def create_host(site_id: str, body: HostIn) -> dict:
    gw = _gw(site_id)
    try:
        out = {"host": gw.create_host(body.host_name, body.folder, body.ipaddress, body.labels)}
        if body.discover:
            out["discovery"] = gw.discover(body.host_name)
        if body.activate:
            out["activation"] = gw.activate()
        return out
    except CheckmkError as exc:
        raise HTTPException(exc.status or 502, str(exc)) from exc
    finally:
        gw.close()


@router.post("/{site_id}/downtimes", status_code=201)
def schedule_downtime(site_id: str, body: DowntimeIn) -> dict:
    gw = _gw(site_id)
    try:
        gw.schedule_downtime(body.host_name, body.minutes, body.comment, body.services)
        return {"ok": True, "site": site_id, "host": body.host_name, "minutes": body.minutes}
    except CheckmkError as exc:
        raise HTTPException(exc.status or 502, str(exc)) from exc
    finally:
        gw.close()


@router.get("/{site_id}/downtimes")
def list_downtimes(site_id: str, host_name: str | None = None) -> list[dict]:
    gw = _gw(site_id)
    try:
        return gw.list_downtimes(host_name)
    except CheckmkError as exc:
        raise HTTPException(exc.status or 502, str(exc)) from exc
    finally:
        gw.close()


@router.delete("/{site_id}/downtimes/{downtime_id}")
def delete_downtime(site_id: str, downtime_id: str) -> dict:
    gw = _gw(site_id)
    try:
        gw.delete_downtime(downtime_id)
        return {"ok": True}
    except CheckmkError as exc:
        raise HTTPException(exc.status or 502, str(exc)) from exc
    finally:
        gw.close()


@router.post("/downtimes/rdm", status_code=201)
def downtime_por_rdm(body: RdmIn) -> dict:
    """Silêncio em lote vinculado à RDM — mata o storm do tipo 24-25 mai."""
    plan = [i.model_dump() for i in body.plan]
    receipts = rdm_downtime(load_sites(), plan, body.rdm, body.minutes)
    return {"rdm": body.rdm, "receipts": receipts, "ok": all(r["ok"] for r in receipts)}

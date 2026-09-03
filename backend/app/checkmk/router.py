"""Endpoints REST do gateway Checkmk (consumidos pelo painel CORVO)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.checkmk.gateway import (
    COLUNAS_SERVICO,
    CheckmkError,
    Gateway,
    agendar_downtime,
    listar_downtimes,
    listar_servicos,
    load_sites,
    rdm_downtime,
    remover_downtimes,
)

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


class DowntimeNovo(BaseModel):
    """Novo downtime. Sem ``servicos`` → silencia o host inteiro."""

    site: str
    host_name: str
    minutes: int = Field(gt=0, le=7 * 24 * 60)
    comment: str = Field(min_length=1)
    servicos: list[str] | None = None


class DowntimeAlvo(BaseModel):
    """Item a remover. ``host``/``servico`` vêm da listagem e permitem a
    remoção alternativa quando o ID sozinho não resolve."""

    site: str
    id: str
    host: str | None = None
    servico: str | None = None


class RemocaoIn(BaseModel):
    alvos: list[DowntimeAlvo] = Field(min_length=1)
    forcar_por_host: bool = False
    """Autoriza a remoção por host quando o ID não resolve — apaga TODOS os
    downtimes do host. Sem isso, o recibo só avisa quantos seriam atingidos."""


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


@router.get("/downtimes")
def downtimes_federados(
    site: str | None = None,
    host: str | None = None,
    tipo: str = Query("all", pattern="^(all|service|host)$"),
    servico: str | None = None,
) -> dict:
    """Downtimes ativos de todos os sites (ou de um), já normalizados.

    ``tipo=service`` responde a pergunta do plantão: *quais serviços estão
    silenciados agora*. Sites indisponíveis viram entradas em ``erros`` — a
    listagem não falha por causa de um site fora.
    """
    return listar_downtimes(load_sites(), site_id=site, host_name=host, tipo=tipo, servico=servico)


@router.get("/services")
def servicos_federados(
    host: str,
    site: str | None = None,
    columns: Annotated[list[str] | None, Query()] = None,
) -> dict:
    """Serviços monitorados de um host, em um site ou em todos.

    É a leitura que fecha o ciclo do p3kill: *o INC foi corrigido ou não?* —
    estado do serviço antes e depois da correção, sem tocar em nada.

    Sem ``site`` varre todos os registrados. O site ``redes`` é central e cobre
    tesp2, tesp03, tece01 e tbsp02, então o site do host nem sempre se deduz do
    nome dele; nessa varredura, host inexistente num site vira entrada em
    ``erros``, o que é esperado.
    """
    return listar_servicos(load_sites(), host_name=host, site_id=site, columns=columns)


@router.post("/downtimes", status_code=201)
def criar_downtime(body: DowntimeNovo) -> dict:
    """Silencia um host inteiro ou serviços específicos dele."""
    try:
        return agendar_downtime(
            load_sites(),
            body.site,
            body.host_name,
            body.minutes,
            body.comment,
            body.servicos,
        )
    except CheckmkError as exc:
        raise HTTPException(exc.status or 502, str(exc)) from exc


@router.post("/downtimes/remover")
def remover(body: RemocaoIn) -> dict:
    """Remove downtimes em lote e confere: ``ok`` reflete o estado real.

    A API do Checkmk responde 204 mesmo quando não remove nada, então cada
    item é relido depois da remoção. Quando o ID não resolve (site que federa
    outro core), o recibo vem com ``requer_confirmacao`` e o número de
    downtimes do mesmo host que a remoção por host levaria junto — reenvie com
    ``forcar_por_host`` para autorizar.
    """
    recibos = remover_downtimes(
        load_sites(),
        [a.model_dump() for a in body.alvos],
        forcar_por_host=body.forcar_por_host,
    )
    return {"recibos": recibos, "ok": all(r["ok"] for r in recibos)}


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


@router.get("/{site_id}/services")
def list_services(
    site_id: str,
    host: str,
    columns: Annotated[list[str] | None, Query()] = None,
) -> list[dict]:
    """Serviços monitorados de um host num site — leitura do core, nunca escrita.

    Achatado como o gateway devolve (só ``extensions``), para o consumidor não
    precisar conhecer o envelope da REST do Checkmk.
    """
    gw = _gw(site_id)
    try:
        return gw.list_services_monitorados(host, columns or COLUNAS_SERVICO)
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

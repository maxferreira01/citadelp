"""Endpoints do Corvo (raio-x consumirá o JSON do scanner agendado)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.corvo.scanner import parse_attachment

router = APIRouter(prefix="/corvo", tags=["Corvo · sinais"])


class Blob(BaseModel):
    blob: str


@router.post("/parse")
def parse(body: Blob) -> dict:
    """Valida o parser contra um attachment cru (uso em debug/ingest)."""
    out = parse_attachment(body.blob)
    return {"parsed": out is not None, "alert": out}

"""CITADEL API — entrada da plataforma."""

from fastapi import FastAPI

from app.checkmk.router import router as checkmk_router
from app.corvo.router import router as corvo_router

app = FastAPI(
    title="CITADEL API",
    version="0.1.0",
    description="Plataforma interna de infraestrutura — TOTVS Cloud. "
    "Corvo (sinais) · gateway Checkmk federado.",
)
app.include_router(corvo_router)
app.include_router(checkmk_router)


@app.get("/healthz", tags=["infra"])
def healthz() -> dict:
    return {"ok": True, "service": "citadel-api"}

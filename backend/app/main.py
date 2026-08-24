"""CITADEL API — entrada da plataforma."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.aci.router import router as aci_router
from app.auth.router import router as auth_router
from app.checkmk.router import router as checkmk_router
from app.corvo.router import router as corvo_router

app = FastAPI(
    title="CITADEL API",
    version="0.1.0",
    description="Plataforma interna de infraestrutura — TOTVS Cloud. "
    "Corvo (sinais) · gateway Checkmk federado.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+):5173",
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(corvo_router)
app.include_router(checkmk_router)
app.include_router(aci_router)


@app.get("/healthz", tags=["infra"])
def healthz() -> dict:
    return {"ok": True, "service": "citadel-api"}

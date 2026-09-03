"""CITADEL API — entrada da plataforma (API + painel)."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.aci.router import router as aci_router
from app.auth.router import router as auth_router
from app.checkmk.router import router as checkmk_router
from app.corvo.router import router as corvo_router
from app.nsx.router import router as nsx_router


class ApiPrefix:
    """Aceita ``/api/<rota>`` como sinônimo de ``/<rota>``.

    A SPA chama a API sob ``/api`` (mesmo caminho do proxy do Vite em dev);
    consumidores externos (p3kill, scripts) seguem chamando a raiz. Os routers
    não mudam — só o caminho é reescrito antes do roteamento.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/api/"):
            scope = dict(scope)
            scope["path"] = scope["path"][4:]
            scope["raw_path"] = scope["path"].encode()
        await self.app(scope, receive, send)


app = FastAPI(
    title="CITADEL API",
    version="0.1.0",
    description="Plataforma interna de infraestrutura — TOTVS Cloud. "
    "Corvo (sinais) · gateway Checkmk federado · capacity de T1 NSX · painel.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+):5173",
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiPrefix)
app.include_router(auth_router)
app.include_router(corvo_router)
app.include_router(checkmk_router)
app.include_router(aci_router)
app.include_router(nsx_router)


@app.get("/healthz", tags=["infra"])
def healthz() -> dict:
    return {"ok": True, "service": "citadel-api"}


# Painel: o build do Vite (frontend/dist) servido pela própria API, quando existir.
# Montado por último: as rotas da API (e /docs) têm precedência.
STATIC_DIR = Path(
    os.environ.get("CITADEL_STATIC_DIR")
    or Path(__file__).resolve().parents[2] / "frontend" / "dist"
)
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="painel")

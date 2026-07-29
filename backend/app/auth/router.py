"""Endpoints de autenticação (login Google → sessão CITADEL)."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.auth.google import (
    AuthError,
    client_id,
    issue_session,
    read_session,
    verify_google_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginIn(BaseModel):
    credential: str
    """ID token emitido pelo Google Identity Services no navegador."""


@router.get("/config")
def config() -> dict:
    """O frontend consulta aqui se o login Google está habilitado."""
    cid = client_id()
    return {"google": bool(cid), "google_client_id": cid}


@router.post("/google")
def login_google(body: GoogleLoginIn) -> dict:
    try:
        profile = verify_google_token(body.credential)
        return {"token": issue_session(profile), "user": profile}
    except AuthError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@router.get("/me")
def me(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "sem token")
    try:
        return read_session(authorization.removeprefix("Bearer "))
    except AuthError as exc:
        raise HTTPException(exc.status, str(exc)) from exc

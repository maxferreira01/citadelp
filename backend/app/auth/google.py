"""Google auth — verificação de ID token (login) e sessão assinada.

Duas credenciais distintas, ambas fora do git:
· GOOGLE_CLIENT_ID — OAuth Client ID (tipo Web) que o frontend usa no botão
  "Entrar com Google"; o backend valida o ID token contra ele.
· GOOGLE_SERVICE_ACCOUNT_FILE — service account p/ chamadas server-side às
  APIs Google (Sheets/BigQuery etc.); não serve para login de usuário.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

SESSION_TTL = 12 * 3600


class AuthError(Exception):
    def __init__(self, msg: str, status: int = 401):
        super().__init__(msg)
        self.status = status


def _secret() -> bytes:
    s = os.environ.get("CITADEL_SESSION_SECRET")
    if not s:
        raise AuthError("CITADEL_SESSION_SECRET ausente no ambiente", 503)
    return s.encode()


def client_id() -> str | None:
    return os.environ.get("GOOGLE_CLIENT_ID") or None


def service_account_info() -> dict | None:
    """Credencial de service account, se configurada (uso server-side)."""
    path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not path or not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def verify_google_token(token: str) -> dict:
    """Valida o ID token do Google e devolve o perfil essencial."""
    cid = client_id()
    if not cid:
        raise AuthError("GOOGLE_CLIENT_ID não configurado no backend", 503)
    try:
        info = google_id_token.verify_oauth2_token(token, google_requests.Request(), cid)
    except ValueError as exc:
        raise AuthError(f"ID token inválido: {exc}") from exc
    return {"email": info["email"], "name": info.get("name", ""), "picture": info.get("picture", "")}


def _sign(payload: bytes) -> str:
    return hmac.new(_secret(), payload, hashlib.sha256).hexdigest()


def issue_session(profile: dict) -> str:
    body = base64.urlsafe_b64encode(
        json.dumps({**profile, "exp": int(time.time()) + SESSION_TTL}).encode()
    ).decode()
    return f"{body}.{_sign(body.encode())}"


def read_session(token: str) -> dict:
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        raise AuthError("token malformado") from None
    if not hmac.compare_digest(sig, _sign(body.encode())):
        raise AuthError("assinatura inválida")
    data = json.loads(base64.urlsafe_b64decode(body))
    if data.get("exp", 0) < time.time():
        raise AuthError("sessão expirada")
    return data

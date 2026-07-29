"""Sessão assinada — emitir, ler, rejeitar adulteração e expiração."""

import time

import pytest

from app.auth import google as auth


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("CITADEL_SESSION_SECRET", "teste-secreto")


def test_sessao_roundtrip():
    tok = auth.issue_session({"email": "m.ferreira@totvs.com.br", "name": "Max"})
    data = auth.read_session(tok)
    assert data["email"] == "m.ferreira@totvs.com.br"
    assert data["exp"] > time.time()


def test_sessao_adulterada_rejeitada():
    tok = auth.issue_session({"email": "a@b.c"})
    body, sig = tok.rsplit(".", 1)
    with pytest.raises(auth.AuthError):
        auth.read_session(body + "x." + sig)


def test_sessao_expirada(monkeypatch):
    monkeypatch.setattr(auth, "SESSION_TTL", -1)
    tok = auth.issue_session({"email": "a@b.c"})
    with pytest.raises(auth.AuthError, match="expirada"):
        auth.read_session(tok)


def test_login_sem_client_id_da_503(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    with pytest.raises(auth.AuthError) as exc:
        auth.verify_google_token("qualquer")
    assert exc.value.status == 503

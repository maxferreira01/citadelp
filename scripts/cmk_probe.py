#!/usr/bin/env python3
"""Sondagem inicial de um site Checkmk para o módulo CITADEL·CORVO.

Uso: python scripts/cmk_probe.py <url-do-site> [--user U] [--secret S]
  ex.: python scripts/cmk_probe.py https://cmk-tesp05.interno/tesp05

Testa autenticação (Bearer user secret), versão da API, navegação na pasta
"redes" (folder_config) e disponibilidade dos endpoints de métricas usados
no relatório de consumo. Somente leitura — não cria nem altera nada.
"""

from __future__ import annotations

import argparse
import sys

import httpx


def req(c: httpx.Client, method: str, path: str, **kw) -> httpx.Response:
    r = c.request(method, path, **kw)
    print(f"  {method} {path} -> {r.status_code}")
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="https://host/site (sem /check_mk)")
    ap.add_argument("--user", default="citadel_api1")
    ap.add_argument("--secret", required=True)
    ap.add_argument("--insecure", action="store_true", help="ignora TLS (labs)")
    a = ap.parse_args()

    base = a.url.rstrip("/") + "/check_mk/api/1.0"
    c = httpx.Client(
        base_url=base,
        headers={
            "Authorization": f"Bearer {a.user} {a.secret}",
            "Accept": "application/json",
        },
        timeout=15,
        verify=not a.insecure,
    )

    print(f"== {base} (user={a.user})")

    r = req(c, "GET", "/version")
    if r.status_code == 401:
        print("!! 401: credencial recusada — conferir user/secret (automation secret)")
        return 1
    if r.status_code >= 400:
        print(f"!! {r.text[:300]}")
        return 1
    v = r.json()
    print(
        f"   Checkmk {v.get('versions', {}).get('checkmk')} · edição {v.get('edition')}"
    )

    print("-- pastas na raiz")
    r = req(
        c,
        "GET",
        "/domain-types/folder_config/collections/all",
        params={"parent": "/", "recursive": "false"},
    )
    folders = [f["id"] for f in r.json().get("value", [])] if r.is_success else []
    print(f"   {folders}")

    redes = next((f for f in folders if "rede" in f.lower()), None)
    if redes:
        print(f"-- conteúdo de {redes!r} (recursivo)")
        r = req(
            c,
            "GET",
            "/domain-types/folder_config/collections/all",
            params={"parent": redes, "recursive": "true"},
        )
        for f in r.json().get("value", []):
            print(f"   {f['id']}  ({f['title']})")
        r = req(
            c,
            "GET",
            "/domain-types/host_config/collections/all",
            params={"include_links": "false"},
        )
        hosts = [
            h["id"]
            for h in r.json().get("value", [])
            if r.is_success
            and h.get("extensions", {}).get("folder", "").startswith(redes)
        ]
        print(f"   hosts na pasta: {len(hosts)} (5 primeiros: {hosts[:5]})")

    print("-- métricas (relatório de consumo)")
    req(
        c,
        "POST",
        "/domain-types/metric/actions/get/invoke",
        json={
            "type": "single_metric",
            "time_range": {"start": "now-4h", "end": "now"},
            "site": "",
            "host_name": "__probe__",
            "service_description": "CPU load",
            "metric_id": "load1",
        },
    )
    print(
        "   (404 no endpoint = versão sem API de métricas; 400/404 de host = endpoint OK)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

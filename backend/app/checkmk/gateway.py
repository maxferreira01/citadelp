"""CITADEL · CORVO — gateway federador da REST API do Checkmk.

Cada edge tem seu próprio site Checkmk (descentralizado). Este gateway registra
os sites via variável de ambiente e normaliza as operações que o Citadel expõe:
criar hosts/monitorações, rodar service discovery, ativar mudanças e
agendar/remover downtimes (inclusive em lote, vinculados a uma RDM — resposta
direta ao storm de 24-25 mai, quando o silêncio por schedule falhou).

Autenticação: automation user por site, header ``Authorization: Bearer user secret``
(formato da REST API 2.x). Credenciais SÓ via ambiente — nunca no repositório.

Config (JSON em CITADEL_CHECKMK_SITES):
    [{"id": "tesp03", "url": "https://cmk-tesp03.interno/tesp03",
      "user": "citadel_api", "secret": "..."}]
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

BRT = timezone(timedelta(hours=-3))


class CheckmkError(RuntimeError):
    """Erro de API com contexto do site e do endpoint."""

    def __init__(self, site: str, detail: str, status: int | None = None):
        super().__init__(f"[{site}] {detail}")
        self.site, self.status = site, status


@dataclass(frozen=True)
class Site:
    id: str
    url: str  # https://host/site (sem /check_mk)
    user: str
    secret: str

    @property
    def base(self) -> str:
        return self.url.rstrip("/") + "/check_mk/api/1.0"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.user} {self.secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


def load_sites(env: str | None = None) -> dict[str, Site]:
    raw = env if env is not None else os.environ.get("CITADEL_CHECKMK_SITES", "[]")
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CheckmkError("registry", f"CITADEL_CHECKMK_SITES inválido: {exc}") from exc
    return {s["id"]: Site(**s) for s in items}


PREFIXO_SERVICO = "Downtime for service: "
PREFIXO_HOST = "Downtime for host: "


def normalizar_downtime(site_id: str, item: dict) -> dict:
    """Achata um downtime da API num registro plano, com o serviço extraído.

    O nome do serviço só existe no ``title``; ``extensions`` traz apenas o
    ``is_service``. Sem isso o painel não consegue mostrar *qual* serviço está
    silenciado — que é a pergunta que o operador faz.
    """
    ext = item.get("extensions", {})
    titulo = item.get("title", "")
    is_service = ext.get("is_service") == "yes"
    servico = None
    if is_service and titulo.startswith(PREFIXO_SERVICO):
        servico = titulo[len(PREFIXO_SERVICO) :]
    return {
        "site": site_id,
        "id": item.get("id"),
        "host": ext.get("host_name"),
        "servico": servico,
        "tipo": "service" if is_service else "host",
        "autor": ext.get("author"),
        "comentario": ext.get("comment"),
        "inicio": ext.get("start_time"),
        "fim": ext.get("end_time"),
        "recorrente": ext.get("recurring") == "yes",
    }


class Gateway:
    """Cliente por site. ``transport`` injetável para testes (MockTransport)."""

    def __init__(
        self,
        site: Site,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 20.0,
    ):
        self.site = site
        self._c = httpx.Client(
            base_url=site.base,
            headers=site.headers,
            timeout=timeout,
            transport=transport,
            verify=True,
        )

    # ------------------------------------------------------------------ util
    def _req(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | list[tuple[str, str]] | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        try:
            r = self._c.request(method, path, json=json_body, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise CheckmkError(self.site.id, f"falha de rede em {path}: {exc}") from exc
        if r.status_code >= 400:
            raise CheckmkError(
                self.site.id, f"{method} {path} → {r.status_code}: {r.text[:300]}", r.status_code
            )
        return r.json() if r.content else {}

    # ------------------------------------------------- hosts / monitorações
    def create_host(
        self,
        host_name: str,
        folder: str = "/",
        ipaddress: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> dict:
        """Cria o host (nova monitoração). Depois: discover() + activate()."""
        attrs: dict[str, Any] = {}
        if ipaddress:
            attrs["ipaddress"] = ipaddress
        if labels:
            attrs["labels"] = labels
        return self._req(
            "POST",
            "/domain-types/host_config/collections/all",
            json_body={"folder": folder, "host_name": host_name, "attributes": attrs},
        )

    def discover(self, host_name: str, mode: str = "fix_all") -> dict:
        """Service discovery (fix_all = aceita novos serviços e remove sumidos)."""
        return self._req(
            "POST",
            "/domain-types/service_discovery_run/actions/start/invoke",
            json_body={"host_name": host_name, "mode": mode},
        )

    def activate(self, force_foreign: bool = False) -> dict:
        """Ativa mudanças pendentes no site (If-Match "*" cobre o ETag exigido)."""
        return self._req(
            "POST",
            "/domain-types/activation_run/actions/activate-changes/invoke",
            json_body={"redirect": False, "sites": [], "force_foreign_changes": force_foreign},
            headers={"If-Match": "*"},
        )

    # ------------------------------------------------- versão / hosts / regras
    def get_version(self) -> dict:
        """Versão/edição do site. 404 aqui = site sem REST API (Checkmk 1.5)."""
        return self._req("GET", "/version")

    def list_hosts(self) -> list[dict]:
        """Hosts configurados no site: [{"id": ..., "folder": ...}]."""
        try:
            data = self._req(
                "GET",
                "/domain-types/host_config/collections/all",
                params={"include_links": "false"},
            )
        except CheckmkError as exc:
            # Sites 2.1 e anteriores não conhecem include_links (400 Unknown
            # field) — repete sem o parâmetro; a resposta só vem maior.
            if exc.status != 400 or "include_links" not in str(exc):
                raise
            data = self._req("GET", "/domain-types/host_config/collections/all")
        return [
            {"id": h.get("id"), "folder": h.get("extensions", {}).get("folder", "")}
            for h in data.get("value", [])
        ]

    def get_ruleset(self, name: str) -> dict:
        """Metadados de um ruleset — sonda se ele existe nesta versão do site."""
        return self._req("GET", f"/objects/ruleset/{name.replace(':', '%3A')}")

    def list_rules(self, ruleset: str) -> list[dict]:
        data = self._req(
            "GET",
            "/domain-types/rule/collections/all",
            params={"ruleset_name": ruleset},
        )
        out = []
        for r in data.get("value", []):
            ext = r.get("extensions", {})
            out.append(
                {
                    "id": r.get("id"),
                    "ruleset": ext.get("ruleset"),
                    "folder": ext.get("folder"),
                    "properties": ext.get("properties", {}),
                    "value_raw": ext.get("value_raw"),
                    "conditions": ext.get("conditions", {}),
                }
            )
        return out

    def create_rule(
        self,
        ruleset: str,
        value_raw: str,
        conditions: dict,
        description: str,
        comment: str = "",
        folder: str = "~",
    ) -> dict:
        return self._req(
            "POST",
            "/domain-types/rule/collections/all",
            json_body={
                "ruleset": ruleset,
                "folder": folder,
                "properties": {"disabled": False, "description": description, "comment": comment},
                "value_raw": value_raw,
                "conditions": conditions,
            },
        )

    def move_rule(self, rule_id: str, folder: str = "~") -> dict:
        """Move a regra para o TOPO da pasta. Rulesets first-match (como
        extra_service_conf) são anulados por regras genéricas que venham
        antes — caso real: regra global '1' sem condições no tesp4."""
        return self._req(
            "POST",
            f"/objects/rule/{rule_id}/actions/move/invoke",
            json_body={"position": "top_of_folder", "folder": folder},
        )

    def delete_rule(self, rule_id: str) -> dict:
        return self._req("DELETE", f"/objects/rule/{rule_id}", headers={"If-Match": "*"})

    def list_services_monitorados(self, host_name: str, columns: list[str]) -> list[dict]:
        """Serviços do host no CORE (endpoint de monitoração, não de config).

        Serve dois momentos: pré-apply (o serviço "Interface X" existe mesmo?)
        e pós-apply (notifications_enabled ficou 0 nos alvos e 1 nos uplinks?).
        """
        params = [("columns", c) for c in columns]
        data = self._req("GET", f"/objects/host/{host_name}/collections/services", params=params)
        return [x.get("extensions", {}) for x in data.get("value", [])]

    # -------------------------------------------------------------- downtimes
    def schedule_downtime(
        self,
        host_name: str,
        minutes: int,
        comment: str,
        services: list[str] | None = None,
        start: datetime | None = None,
    ) -> dict:
        """Downtime de host (services=None) ou de serviços específicos."""
        t0 = (start or datetime.now(BRT)).isoformat()
        t1 = ((start or datetime.now(BRT)) + timedelta(minutes=minutes)).isoformat()
        if services:
            body = {
                "downtime_type": "service",
                "host_name": host_name,
                "service_descriptions": services,
                "start_time": t0,
                "end_time": t1,
                "comment": comment,
            }
            path = "/domain-types/downtime/collections/service"
        else:
            body = {
                "downtime_type": "host",
                "host_name": host_name,
                "start_time": t0,
                "end_time": t1,
                "comment": comment,
            }
            path = "/domain-types/downtime/collections/host"
        return self._req("POST", path, json_body=body)

    def list_downtimes(
        self,
        host_name: str | None = None,
        tipo: str = "all",
        servico: str | None = None,
    ) -> list[dict]:
        """Downtimes normalizados do site. ``tipo``: all | service | host.

        A API não expõe ``service_description`` como campo próprio: o nome do
        serviço vem no ``title`` ("Downtime for service: X") e o que distingue
        host de serviço é ``is_service``. Também não filtra por ``host_name``
        na querystring (aceita, mas ignora) — daí os filtros irem no ``query``
        em expressão Livestatus.
        """
        exprs: list[dict] = []
        if host_name:
            exprs.append({"op": "=", "left": "downtimes.host_name", "right": host_name})
        if tipo in ("service", "host"):
            valor = "1" if tipo == "service" else "0"
            exprs.append({"op": "=", "left": "downtimes.is_service", "right": valor})
        params = None
        if exprs:
            q = exprs[0] if len(exprs) == 1 else {"op": "and", "expr": exprs}
            params = {"query": json.dumps(q)}

        data = self._req("GET", "/domain-types/downtime/collections/all", params=params)
        itens = [normalizar_downtime(self.site.id, x) for x in data.get("value", [])]
        if servico:
            alvo = servico.lower()
            itens = [i for i in itens if i["servico"] and alvo in i["servico"].lower()]
        return itens

    def delete_downtime(self, downtime_id: str) -> dict:
        """Remove por ID. Atenção: a API responde 204 mesmo quando não remove
        (ver ``remover_downtimes``) — sempre confira depois."""
        return self._req(
            "POST",
            "/domain-types/downtime/actions/delete/invoke",
            json_body={"delete_type": "by_id", "downtime_id": str(downtime_id)},
        )

    def delete_downtime_por_params(self, host_name: str, services: list[str] | None = None) -> dict:
        """Remove por host/serviço em vez de ID — alcança downtimes que o
        ``by_id`` não pega quando o objeto pertence a outro site."""
        body: dict[str, Any] = {"delete_type": "params", "host_name": host_name}
        if services:
            body["service_descriptions"] = services
        return self._req("POST", "/domain-types/downtime/actions/delete/invoke", json_body=body)

    def close(self) -> None:
        self._c.close()


def listar_downtimes(
    sites: dict[str, Site],
    site_id: str | None = None,
    host_name: str | None = None,
    tipo: str = "all",
    servico: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Downtimes de todos os sites (ou de um só), com erro por site isolado.

    Um site fora do ar não derruba a listagem — vira uma entrada em ``erros``,
    para o painel mostrar o que conseguiu ler e o que faltou.
    """
    alvos = {site_id: sites[site_id]} if site_id and site_id in sites else sites
    if site_id and site_id not in sites:
        return {"itens": [], "erros": [{"site": site_id, "erro": "site não registrado"}]}

    itens: list[dict] = []
    erros: list[dict] = []
    for sid, site in alvos.items():
        gw = Gateway(site, transport=transport)
        try:
            itens.extend(gw.list_downtimes(host_name=host_name, tipo=tipo, servico=servico))
        except CheckmkError as exc:
            erros.append({"site": sid, "erro": str(exc)})
        finally:
            gw.close()
    itens.sort(key=lambda i: (i["site"], i["host"] or "", i["servico"] or ""))
    return {"itens": itens, "erros": erros, "total": len(itens)}


COLUNAS_SERVICO = [
    "description",
    "state",
    "last_check",
    "plugin_output",
    "acknowledged",
    "notifications_enabled",
    "last_state_change",
]


def listar_servicos(
    sites: dict[str, Site],
    host_name: str,
    site_id: str | None = None,
    columns: list[str] | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Serviços monitorados de um host, em um site ou em todos, com erro isolado.

    Sem ``site_id`` varre todos os sites registrados: o site ``redes`` é central
    e cobre 4 datacenters, então nem sempre dá para deduzir onde o host está a
    partir do nome dele. Site fora do ar vira entrada em ``erros`` — a consulta
    não falha por causa de um site indisponível.

    Um host que não existe naquele site responde 404 e entra em ``erros``, o que
    é esperado ao varrer todos.
    """
    if site_id and site_id not in sites:
        erro = {"site": site_id, "erro": "site não registrado"}
        return {"itens": [], "erros": [erro], "total": 0}
    alvos = {site_id: sites[site_id]} if site_id else sites

    itens: list[dict] = []
    erros: list[dict] = []
    for sid, site in alvos.items():
        gw = Gateway(site, transport=transport)
        try:
            for s in gw.list_services_monitorados(host_name, columns or COLUNAS_SERVICO):
                itens.append({"site": sid, "host": host_name, **s})
        except CheckmkError as exc:
            erros.append({"site": sid, "erro": str(exc)})
        finally:
            gw.close()
    itens.sort(key=lambda i: (i["site"], str(i.get("description") or "")))
    return {"itens": itens, "erros": erros, "total": len(itens)}


def _sobreviveu(gw: Gateway, host: str | None, downtime_id: Any) -> bool:
    """O downtime ainda está lá depois da tentativa de remoção?

    Sem o host não há como reconferir (a listagem é por host) — nesse caso
    acredita no 204 da API.
    """
    if not host:
        return False
    return any(str(i["id"]) == str(downtime_id) for i in gw.list_downtimes(host_name=host))


def _sobreviveu_apos_espera(
    gw: Gateway, host: str | None, downtime_id: Any, tentativas: int, espera: float
) -> bool:
    """Igual a ``_sobreviveu``, mas insiste antes de dar o veredito negativo.

    A listagem é eventualmente consistente: um downtime removido pode continuar
    aparecendo por alguns segundos (mais ainda quando pertence a um site
    remoto). Só o caminho de FALHA paga essa espera — se já sumiu na primeira
    leitura, retorna na hora.
    """
    for i in range(tentativas):
        if not _sobreviveu(gw, host, downtime_id):
            return False
        if i < tentativas - 1 and espera:
            time.sleep(espera)
    return True


def remover_downtimes(
    sites: dict[str, Site],
    alvos: list[dict],
    transport: httpx.BaseTransport | None = None,
    tentativas: int = 3,
    espera: float = 2.0,
    forcar_por_host: bool = False,
) -> list[dict]:
    """Remove downtimes em lote, CONFERINDO o resultado.

    ``alvos``: [{"site": "tesp3", "id": "1713", "host": "fw01", "servico": "CPU"}]

    Três comportamentos do ambiente moldam esta função — todos verificados
    contra os sites reais:

    1. ``by_id`` só funciona quando o downtime está no core do site consultado.
       Num site que federa outros (o ``central`` daqui, cujo core local está
       vazio), a API responde 204 e não remove nada.
    2. A remoção por params **ignora** ``service_descriptions`` nesta versão:
       passar o serviço não remove. Só a remoção por host funciona — e ela
       apaga TODOS os downtimes daquele host.
    3. A listagem é eventualmente consistente (segundos de atraso), então uma
       releitura isolada pode dar falso negativo.

    Por (2), a alternativa não é aplicada sozinha: quando o ``by_id`` não
    resolve, o recibo explica quantos outros downtimes do mesmo host seriam
    atingidos e exige ``forcar_por_host`` para prosseguir. Silenciar o alerta
    de outra pessoa por engano é pior do que falhar de forma explícita.
    """
    recibos: list[dict] = []
    for alvo in alvos:
        sid, did = alvo.get("site"), alvo.get("id")
        host = alvo.get("host")
        if sid not in sites:
            recibos.append({"site": sid, "id": did, "ok": False, "erro": "site não registrado"})
            continue

        gw = Gateway(sites[sid], transport=transport)
        try:
            erro_api: str | None = None
            try:
                gw.delete_downtime(str(did))
            except CheckmkError as exc:
                erro_api = str(exc)

            # paciência aqui também: logo após o delete a listagem ainda pode
            # mostrar o item por alguns segundos e mandaria o fluxo para a
            # remoção por host sem necessidade
            if not _sobreviveu_apos_espera(gw, host, did, tentativas, espera):
                recibos.append({"site": sid, "id": did, "ok": True, "via": "by_id"})
                continue
            if not host:
                recibos.append(
                    {"site": sid, "id": did, "ok": False, "erro": erro_api or "ainda presente"}
                )
                continue

            outros = [i for i in gw.list_downtimes(host_name=host) if str(i["id"]) != str(did)]
            if not forcar_por_host:
                recibos.append(
                    {
                        "site": sid,
                        "id": did,
                        "ok": False,
                        "requer_confirmacao": True,
                        "colaterais": len(outros),
                        "erro": (
                            f"não sai por ID neste site (downtime federado de outro core). "
                            f"A remoção que funciona aqui é por host e apagaria também "
                            f"{len(outros)} outro(s) downtime(s) de '{host}' — reenvie com "
                            f"forcar_por_host=true para confirmar."
                        ),
                    }
                )
                continue

            try:
                gw.delete_downtime_por_params(host)  # sem serviços: só assim remove
            except CheckmkError as exc:
                erro_api = str(exc)

            if _sobreviveu_apos_espera(gw, host, did, tentativas, espera):
                recibos.append(
                    {
                        "site": sid,
                        "id": did,
                        "ok": False,
                        "erro": erro_api or "não removido nem por host — verificar pela GUI",
                    }
                )
            else:
                recibos.append(
                    {
                        "site": sid,
                        "id": did,
                        "ok": True,
                        "via": "por_host",
                        "colaterais": [i["id"] for i in outros],
                    }
                )
        except CheckmkError as exc:
            recibos.append({"site": sid, "id": did, "ok": False, "erro": str(exc)})
        finally:
            gw.close()
    return recibos


def agendar_downtime(
    sites: dict[str, Site],
    site_id: str,
    host_name: str,
    minutes: int,
    comment: str,
    services: list[str] | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict:
    """Agenda downtime de host (services=None) ou de serviços num site."""
    if site_id not in sites:
        raise CheckmkError(site_id, "site não registrado")
    gw = Gateway(sites[site_id], transport=transport)
    try:
        gw.schedule_downtime(host_name, minutes, comment, services)
        return {
            "ok": True,
            "site": site_id,
            "host": host_name,
            "servicos": services,
            "minutos": minutes,
        }
    finally:
        gw.close()


def rdm_downtime(
    sites: dict[str, Site],
    plan: list[dict],
    rdm: str,
    minutes: int,
    transport: httpx.BaseTransport | None = None,
) -> list[dict]:
    """Downtime em lote vinculado a uma RDM, cruzando sites descentralizados.

    plan: [{"site": "tesp03", "host": "edge-fw01", "services": ["Float IP"] | None}]
    Retorna um recibo por item (ok/erro) — nunca interrompe o lote no 1º erro.
    """
    receipts: list[dict] = []
    comment = f"RDM {rdm} · downtime via CITADEL"
    for item in plan:
        sid = item["site"]
        if sid not in sites:
            receipts.append(
                {"site": sid, "host": item.get("host"), "ok": False, "error": "site não registrado"}
            )
            continue
        gw = Gateway(sites[sid], transport=transport)
        try:
            gw.schedule_downtime(item["host"], minutes, comment, item.get("services"))
            receipts.append({"site": sid, "host": item["host"], "ok": True, "rdm": rdm})
        except CheckmkError as exc:
            receipts.append({"site": sid, "host": item["host"], "ok": False, "error": str(exc)})
        finally:
            gw.close()
    return receipts

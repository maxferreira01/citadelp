# CITADEL

Plataforma interna de gestão de infraestrutura de redes e datacenters — TOTVS Cloud.
*Veja o limite antes de alcançá-lo.*

Módulos: **Conselho** (visão executiva) · **Três Olhos** (capacidade e previsão) · **Corvo** (sinais e integrações) · **Muralha** (limites de plataforma) · **Domínios** · **Arquivo** · **Tesouro** · **Campanhas** · **Meistre ✦** (assistente).

## Estado atual (v0.1)

| Área | Conteúdo | Procedência |
|---|---|---|
| `frontend/` | SPA completa (login 4b → shell 5a → módulos) | Corvo com dados **OBS** reais da varredura do Slack; demais módulos **EST · mock sinalizado** |
| `backend/` | FastAPI: parser do Corvo + **gateway federado do Checkmk** (hosts, discovery, activate, downtimes, downtime em lote por RDM) | código de produção, testado |
| `collectors/` | Scanner do canal `#alert-float-ip` (Slack API → JSON) · **Corvo · Datadog**: relatório diário do `#datadog-redes` (DM + PDF) e bot de consulta em Socket Mode ([runbook](docs/runbook-corvo-datadog.md)) | produção · novo (ago/2026) |
| `deploy/k8s/` | Deployment/Service da API + CronJob do scanner | base |
| `deploy/systemd/` | Units + install.sh do Corvo · Datadog para a dev-redes | novo |

## Desenvolvimento

```bash
cp .env.example .env        # preencha os segredos (NUNCA commitados)
make setup                  # backend editable + pre-commit hooks
make lint && make test      # mesmo gate do CI
make run                    # API em http://localhost:8000/docs
make build-front            # SPA (Vite)
```

## Gateway Checkmk (sites descentralizados)

Um site Checkmk por edge, registrado em `CITADEL_CHECKMK_SITES` (JSON). Automation
user com **role mínima** por site. Operações expostas em `/checkmk/*`:

- `POST /checkmk/{site}/hosts` — cria monitoração (host + discovery + activate)
- `POST /checkmk/{site}/downtimes` — downtime de host ou serviços
- `POST /checkmk/downtimes/rdm` — **downtime em lote vinculado à RDM**, cruzando
  sites — resposta direta ao storm de 24–25 mai (schedule de silêncio falhou)
- `GET/DELETE /checkmk/{site}/downtimes[...]` — listar/remover

## CI/CD

- **`ci.yml`** — a cada push/PR: gitleaks (segredos), ruff check+format, pytest,
  build do Vite; jobs condicionados por path; job-gate `ci-ok` para branch protection.
- **`release.yml`** — tag `v*`: imagem da API → GHCR (`ghcr.io/<repo>/api`).
- **`security.yml`** — semanal: `pip-audit`, `npm audit --audit-level=high`,
  gitleaks no histórico completo.
- **Dependabot** — pip, npm e actions, semanal, agrupado.
- **pre-commit** — ruff, gitleaks, detect-private-key.

### Configuração única no GitHub (manual)

1. *Settings → Branches*: proteção da `main` exigindo o check **CI ok** e revisão (CODEOWNERS).
2. *Settings → Secrets and variables → Actions*: criar `CITADEL_CHECKMK_SITES` e
   `SLACK_BOT_TOKEN` quando houver deploy via Actions.

## Política de segredos

Credenciais (automation users do Checkmk, token do Slack) vivem **somente** em
`.env` local / Secrets do Actions / Secret do k8s (`citadel-env`). O repositório
é varrido por gitleaks no pre-commit, no CI e semanalmente. Credenciais expostas
em qualquer canal de chat devem ser **rotacionadas imediatamente**.

## Princípios de produto

Trajetória, não só estado · todo dado tem procedência (OBS/CALC/EST/MAN) · todo
sinal leva a uma ação · o desconhecido também é um estado (◌ sem coleta).

# CITADEL

Plataforma interna de gestão de infraestrutura de redes e datacenters — TOTVS Cloud.
*Veja o limite antes de alcançá-lo.*

Módulos: **Conselho** (visão executiva) · **Três Olhos** (capacidade e previsão) · **Corvo** (sinais e integrações) · **Muralha** (limites de plataforma) · **Domínios** · **Arquivo** · **Tesouro** · **Campanhas** · **Meistre ✦** (assistente).

## Estado atual (v0.1)

| Área | Conteúdo | Procedência |
|---|---|---|
| `design-system/` | **CIDADELA Design System** — tokens (`styles.css`), 12 componentes React (`index.js`), kit Login → Três Olhos, specimens HTML, guidelines de marca/domínio, `SKILL.md` | fonte única de identidade visual (decisões de 27/07/2026); o frontend importa daqui via alias `@ds` |
| `frontend/` | SPA completa (login 4b → shell 5a → módulos), **sobre o design system**: tokens + componentes de `@ds`, composições próprias em `src/ui.jsx`, uma pasta por tela (`screens/`) e por módulo (`modules/`) | Corvo com dados **OBS** reais da varredura do Slack; demais módulos **EST · mock sinalizado** |
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
cd frontend && npm run dev  # SPA em dev (proxy /api → :5533)
```

O `design-system/` fica **fora da raiz do Vite** de propósito (é um entregável
próprio, com specimens e skill). O `frontend/vite.config.js` resolve `@ds` para
ele, dedupa `react`/`react-dom` (os componentes do DS importam React de fora de
`frontend/`) e libera `server.fs.allow`. Regras de uso em
[`design-system/readme.md`](design-system/readme.md#uso-no-app-citadelpfrontend).

## Gateway Checkmk (sites descentralizados)

Um site Checkmk por edge, registrado em `CITADEL_CHECKMK_SITES` (JSON). Automation
user com **role mínima** por site. Operações expostas em `/checkmk/*`:

- `POST /checkmk/{site}/hosts` — cria monitoração (host + discovery + activate)
- `POST /checkmk/{site}/downtimes` — downtime de host ou serviços
- `POST /checkmk/downtimes/rdm` — **downtime em lote vinculado à RDM**, cruzando
  sites — resposta direta ao storm de 24–25 mai (schedule de silêncio falhou)
- `GET/DELETE /checkmk/{site}/downtimes[...]` — listar/remover
- `GET /checkmk/{site}/services?host=` — **estado dos serviços monitorados** de
  um host (leitura do core). `GET /checkmk/services?host=` faz o mesmo federado,
  sem precisar saber o site — útil porque o site `redes` é central e cobre 4
  datacenters. É a verificação que o [p3kill](../p3kill/) usa para responder
  *o INC foi corrigido ou não?*

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

# Contexto de build = RAIZ do repo (release.yml usa context: . e file: backend/Dockerfile):
# o painel (frontend + design-system) entra na imagem junto com a API.

# --- estágio 1: build do painel (Vite) ---
FROM node:20-alpine AS web
WORKDIR /web/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# vite.config.js resolve @ds em ../design-system
COPY design-system/ /web/design-system/
RUN npm run build

# --- estágio 2: API + estático ---
FROM python:3.12-slim
WORKDIR /srv
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir . && useradd -r citadel
COPY --from=web /web/frontend/dist /srv/frontend/dist
ENV CITADEL_STATIC_DIR=/srv/frontend/dist
USER citadel
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

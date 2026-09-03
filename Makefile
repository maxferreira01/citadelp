.PHONY: setup lint test run scan up down build-front
setup:            ## instala dependências de dev (backend + hooks)
	pip install -e "backend[dev]" && pre-commit install
lint:             ## ruff check + format
	ruff check backend && ruff format --check backend
test:             ## testes do backend
	pytest backend -q
run:              ## API local (5533 = alvo do proxy do Vite em dev)
	uvicorn app.main:app --app-dir backend --reload --port 5533
scan:             ## caça segredos no working tree
	gitleaks detect --no-git -v || true
build-front:      ## build do frontend
	cd frontend && npm ci && npm run build
up:               ## stack local (api)
	docker compose up --build -d
down:
	docker compose down

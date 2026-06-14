# All Python tooling runs via uv.
.PHONY: sync train test lint build up down

sync:  ; uv sync
train: ; uv run python model/train.py
test:  ; uv run pytest -q
lint:  ; uv run ruff check .
build: ; docker build -f serving/Dockerfile -t rocketml:dev .
up:    ; docker compose -f deploy/compose/docker-compose.yml up --build
down:  ; docker compose -f deploy/compose/docker-compose.yml down

# NOTE: a `deploy` (Helm / Kubernetes) target is intentionally omitted.
# Phase 4 (Kubernetes + Helm) is built by hand as a learning exercise.

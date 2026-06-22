# All Python tooling runs via uv.
.PHONY: sync train test lint build up down traffic

sync:  ; uv sync
train: ; uv run --group train python model/train.py
test:  ; uv run pytest -q
lint:  ; uv run ruff check .
build: ; docker build -f serving/Dockerfile -t rocketml:dev .
up:      ; docker compose -f deploy/compose/docker-compose.yml up --build
down:    ; docker compose -f deploy/compose/docker-compose.yml down
traffic: ; uv run python scripts/fire_traffic.py

# NOTE: a `deploy` (Helm / Kubernetes) target is intentionally omitted.
# Phase 4 (Kubernetes + Helm) is built by hand as a learning exercise.

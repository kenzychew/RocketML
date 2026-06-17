# RocketML

RocketML is a small self-service platform for serving NLP text models. You bring
a trained text classifier; it wraps the model in a REST API (text in,
`{label, score}` out), packages it as a slim container, runs it through CI,
versions it in MLflow, exposes Prometheus metrics, and deploys it to Kubernetes.

The goal is to get a model from trained to deployed-and-monitored without every
team rebuilding the same packaging, CI, and deployment plumbing.

(The product is RocketML; the repository directory is `ml-serving-platform`.)

## What it does

- `POST /predict` takes raw text and returns a label with a confidence score,
  e.g. `{"label": "positive", "score": 0.97}`.
- `GET /health` backs the container healthcheck and the Kubernetes probes;
  `GET /metrics` exposes request count and latency for Prometheus to scrape.
- Runs as a multi-stage, non-root, slim container; dependencies are pinned with
  uv (`uv.lock`), so builds are reproducible.
- The served model is versioned in an MLflow registry, CI lints/tests/builds and
  publishes the image, and Helm rolls it out to Kubernetes.

Right now (Phase 0) the whole path is wired together, but `/predict` returns a
hardcoded stub -- the real model and MLflow integration land in Phase 1.

## How a request flows

    client --POST /predict {"text": ...}--> FastAPI (serving/app)
                                              |
                                              v
                              model (joblib artifact, registered in MLflow)
                                              |
                                              v
                    {"label": ..., "score": ...}  <-- JSON response

    GET /metrics  --scraped by-->  Prometheus  --visualised in-->  Grafana
    git push      --triggers-->    CI: lint -> test -> build -> push (GHCR)
    image         --deployed by--> Helm  -->  Kubernetes

## API

| Method | Path       | Request           | Response                                |
|--------|------------|-------------------|-----------------------------------------|
| POST   | `/predict` | `{"text": "..."}` | `{"label": "positive", "score": 0.97}`  |
| GET    | `/health`  | --                | `{"status": "ok"}`                      |
| GET    | `/metrics` | --                | Prometheus exposition text              |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and, for the container, Docker.

    make sync     # install / refresh dependencies (uv sync)
    make test     # run the tests (uv run pytest)
    make lint     # ruff
    make build    # build the image -> rocketml:dev

Run it locally:

    uv run uvicorn app.main:app --app-dir serving --host 0.0.0.0 --port 8000

    curl -s localhost:8000/health
    curl -s -X POST localhost:8000/predict \
      -H 'content-type: application/json' \
      -d '{"text": "shipping was fast and it works great"}'

Or in a container:

    make build
    docker run --rm -p 8000:8000 rocketml:dev

## Project layout

    ml-serving-platform/
    |-- serving/
    |   |-- app/            # FastAPI service: /health /predict /metrics
    |   |-- tests/          # pytest API tests
    |   \-- Dockerfile      # multi-stage (uv), non-root, healthcheck
    |-- model/              # train + register to MLflow         (Phase 1)
    |-- monitoring/         # Prometheus + Grafana               (Phase 3)
    |-- deploy/             # docker-compose (Phase 3), Helm      (Phase 4)
    |-- docs/               # architecture decision records (ADRs)
    |-- Makefile            # common make targets
    |-- pyproject.toml      # dependencies (uv)
    \-- uv.lock             # pinned versions (committed)

## Roadmap

| Phase | Scope                                              | State       |
|-------|----------------------------------------------------|-------------|
| 0     | Setup + walking skeleton (stub `/predict`)         | in progress |
| 1     | Real model + MLflow tracking / registry            | planned     |
| 2     | CI: lint -> test -> build -> push (GHCR)            | planned     |
| 3     | Local stack + observability (Prometheus + Grafana) | planned     |
| 4     | Kubernetes + Helm (the learning stretch)           | planned     |

## Documentation

- Architecture decisions: `docs/decisions/` (ADRs, added per phase)

## Future extensions

A few things I'd reach for with more time: provisioning the cluster with
Terraform instead of setting it up by hand, ArgoCD so deploys are GitOps-driven,
and Evidently for real text-drift monitoring rather than basic score stats.
Request auth and horizontal autoscaling are the natural next steps once it sees
real traffic.

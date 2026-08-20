# RocketML

A small self-service platform for serving NLP text classifiers as a containerised, CI-built, monitored, Kubernetes-deployed inference API.

[![ci](https://github.com/kenzychew/RocketML/actions/workflows/ci.yml/badge.svg)](https://github.com/kenzychew/RocketML/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.12-blue)
![fastapi](https://img.shields.io/badge/api-fastapi-009688)
![docker](https://img.shields.io/badge/container-docker-2496ed)
![kubernetes](https://img.shields.io/badge/deploy-kubernetes-326ce5)
![helm](https://img.shields.io/badge/chart-helm-0f1689)

**Live demo:** [huggingface.co/spaces/kenzychew/rocketml-sentiment](https://huggingface.co/spaces/kenzychew/rocketml-sentiment) -- type a movie review, get a prediction.

## What this is

You bring a trained text classifier. RocketML wraps it in a REST API (text in, `{label, score}` out), packages it as a slim container, runs it through CI, tracks and registers it in MLflow, exposes Prometheus metrics, and deploys it to Kubernetes with a Helm chart.

I built it because there's a lot of repetitive work between training a model and getting it running live where people can actually use it and watch how it's doing -- packaging it up, testing it automatically, releasing it, and adding monitoring -- and that work is much the same every time. RocketML does that groundwork once so it can be reused for any model. The reusable machinery is the real deliverable; the small sentiment model it ships with is just there to show it working.

## How a request flows

```
  client
    |
    |  POST /predict  {"text": "..."}
    v
  FastAPI (serving/app) ----> model (joblib artifact, registered in MLflow)
    |                                    |
    |  {"label": "...", "score": ...} <--+
    v
  client

  GET /metrics --> scraped by Prometheus --> visualised in Grafana

  git push --> CI: lint --> test --> train --> build --> push (GHCR)
                  |
                  v
              image --> Helm --> Kubernetes (kind)
                                    |
                                    +-- scraped in-cluster via ServiceMonitor
```

## What's inside

The serving app is FastAPI + uvicorn. `POST /predict` runs inference, `GET /health` answers without touching the model, and `GET /metrics` exposes request count, error count, and latency for Prometheus.

The model lives in `model/train.py`: a scikit-learn TF-IDF + LogisticRegression sentiment classifier trained on a 5k IMDB subset, logged and registered to MLflow.

The container is a multi-stage Dockerfile on `python:3.12-slim`, deps installed with uv, running as a non-root user. It bakes the model artifact and loads it with joblib, so there's no MLflow at runtime. Final size is 561 MB.

CI runs on GitHub Actions. Every push and PR runs ruff and pytest. On `main`, it also trains the model, builds the image, and pushes to GHCR.

For local use, Docker Compose brings up serving + MLflow + Prometheus + Grafana with the Grafana dashboard provisioned on startup, plus a small traffic generator. For the Kubernetes path, the Helm chart in `deploy/helm/rocketml` runs the service on a local kind cluster with probes, resource limits, and in-cluster scraping via a ServiceMonitor.

## API

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| POST | `/predict` | `{"text": "..."}` | `{"label": "negative"\|"positive", "score": <float>}` |
| GET | `/health` | none | `{"status": "ok"}` |
| GET | `/metrics` | none | Prometheus text exposition |

`score` is the model's `predict_proba` for the returned label. The metrics are `predict_requests_total`, `predict_errors_total`, and `predict_latency_seconds`.

```
curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"text": "this movie was a complete waste of time"}'
# {"label":"negative","score":0.89}
```

## Live demo

The bundled sentiment model runs publicly in two places:

- **Hugging Face Space:** [huggingface.co/spaces/kenzychew/rocketml-sentiment](https://huggingface.co/spaces/kenzychew/rocketml-sentiment) --
  a small Gradio UI, rate-limited with a per-client cooldown and a daily
  prediction budget ("demo credits"). The `demo/` folder is what the Space
  runs.
- **Railway:** [rocket.kenzychew.com](https://rocket.kenzychew.com) --
  the same model behind a plain FastAPI + static frontend, same rate
  limiting. The `demo-railway/` folder is what this deploy runs.

Both serve the same joblib artifact this repo trains and serves.

## Running it

Install `uv` and Docker. For the Kubernetes path you also need `kind`, `kubectl`, and `helm`. Run `make train` before building the image locally -- the build bakes the trained artifact in.

### 1. Just the API

```
make build
docker run --rm -p 8000:8000 rocketml:dev
# or, without Docker:
uv run uvicorn app.main:app --app-dir serving --host 0.0.0.0 --port 8000
```

### 2. Full local stack (Docker Compose)

Brings up serving, MLflow, Prometheus, and Grafana, with the Grafana dashboard provisioned on startup.

```
make up        # API :8000, MLflow :5000, Prometheus :9090, Grafana :3000
make traffic   # fire a small loop of /predict calls so the dashboard panels move
make down
```

### 3. Kubernetes (kind + Helm + in-cluster monitoring)

```
kind create cluster --name rocketml
make build
kind load docker-image rocketml:dev --name rocketml
helm install rocketml deploy/helm/rocketml

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  --set alertmanager.enabled=false --set nodeExporter.enabled=false
kubectl apply -f deploy/k8s/servicemonitor.yaml
```

Port-forwards:

```
kubectl port-forward svc/rocketml 8000:8000
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Grafana admin password:
kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

Teardown:

```
helm uninstall monitoring -n monitoring
helm uninstall rocketml
kind delete cluster --name rocketml
```

## Project layout

```
serving/             FastAPI app, schemas, model loader, config, tests
  app/               main.py, schemas.py, model_loader.py, config.py, preprocessing.py
  tests/             pytest API tests against a tiny real model (no network)
  Dockerfile         multi-stage, slim, non-root
model/train.py       train, evaluate, log+register to MLflow, write joblib artifact
monitoring/          prometheus.yml + Grafana dashboards and provisioning
deploy/
  compose/           docker-compose.yml for the local stack
  helm/rocketml/     hand-written Helm chart (Deployment, Service, probes)
  k8s/               servicemonitor.yaml for in-cluster scraping
demo/                Gradio app + model artifact for the public HF Space demo
scripts/             fire_traffic.py (load generator)
docs/decisions/      ADRs
Makefile             sync, train, test, lint, build, up, down, traffic
pyproject.toml       deps managed with uv (pinned in uv.lock)
```

## Design decisions

The full reasoning is in `docs/decisions/`. The choices that mattered most:

**The model is small on purpose** ([ADR-0001](docs/decisions/0001-model-and-serving.md)). It's a TF-IDF (1-2 grams, 20k features) + LogisticRegression classifier, accuracy ~0.86 and F1 ~0.87, not a transformer. The artifact is under 1 MB, inference is CPU-instant and deterministic, and the image stays small. A transformer would have inflated the image and dragged in GPU concerns that have nothing to do with what this project is about.

**The container bakes the artifact instead of running MLflow** ([ADR-0001](docs/decisions/0001-model-and-serving.md)). `train.py` handles MLflow (tracking and registry, local sqlite). The serving image bakes the joblib artifact and loads it directly, so the runtime has no MLflow dependency. That dropped the image from 1.23 GB to 561 MB. The full mlflow stack was most of the weight; mlflow-skinny turned out to be a metapackage, so I went with joblib. The loader is config-driven (pydantic-settings, `PRED_MODEL_PATH`), lazy, and cached, which is what keeps `/health` independent of the model load.

**CI trains the model before it builds** ([ADR-0002](docs/decisions/0002-ci-design.md)). On `main`, the `build-and-push` job (gated on the test job via `needs`) trains the model, builds the serving image, and pushes it to `ghcr.io/kenzychew/rocketml/serving` tagged `:latest` and `:<sha>`. The image always carries a freshly trained artifact rather than a binary checked into the repo.

**The Helm chart is hand-written, and scraping uses a ServiceMonitor** ([ADR-0003](docs/decisions/0003-helm-k8s.md)). The chart is written from scratch rather than left as `helm create` output, since the point was to learn what each piece does. In-cluster observability uses kube-prometheus-stack plus a ServiceMonitor for dynamic service discovery instead of a static scrape config. The ADR records what tripped me up along the way: the kind image store and `ImagePullBackOff`, the `requests <= limits` admission rule, the CRD registration race, the ServiceMonitor release label, and port-forward mechanics.

## Roadmap

Phases 0 through 5 are done. Phase 6 is planned.

- [x] Phase 0 -- walking skeleton: containerised FastAPI returning a prediction, one passing test
- [x] Phase 1 -- real model trained, logged, and registered in MLflow; wired into `/predict`
- [x] Phase 2 -- CI: lint, test, train, build, push to GHCR
- [x] Phase 3 -- local Compose stack with Prometheus + Grafana observability (tagged `v1-mvp`)
- [x] Phase 4 -- Helm chart on a kind cluster with in-cluster monitoring
- [x] Phase 5 -- public demo deployment (live Hugging Face Space)
- [ ] Phase 6 -- final polish and narrative

## Future extensions

Where I'd take it next, roughly in order: Terraform for the cluster and supporting infrastructure, ArgoCD for GitOps-style deployment, Evidently for data and prediction drift monitoring, auth and rate limiting on the public endpoint, and horizontal pod autoscaling driven by the latency metrics already exposed.

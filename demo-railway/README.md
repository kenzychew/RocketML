# RocketML -- Railway demo

A second public demo of the same sentiment model, built as plain FastAPI +
a minimal static frontend instead of Gradio, for a single-service Railway
deploy. This folder is self-contained: it vendors serving/app's model
loading and `/predict` logic (see `app/__init__.py` for why they're copied
rather than imported) and bundles its own copy of the joblib artifact under
`model/`, the same way `demo/` bundles its own copy for the Hugging Face
Space.

This is deployed and live on Railway at https://rocket.kenzychew.com.

## Run locally

```
cd demo-railway
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-demo.txt
uvicorn main:app --reload
```

Open http://localhost:8000 for the frontend, or call the API directly:

```
curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"text": "this movie was a complete waste of time"}'
# {"label":"negative","score":0.89}
```

## Run with Docker

```
docker build -t rocketml-demo-railway .
docker run --rm -p 8000:8000 rocketml-demo-railway
```

## Config (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `PRED_MODEL_PATH` | `model/sentiment.joblib` | Path to the joblib artifact |
| `DEMO_DAILY_CAP` | `200` | Global daily prediction cap |
| `DEMO_COOLDOWN_SECONDS` | `3.0` | Per-client cooldown between predictions |
| `PORT` | `8000` | Port uvicorn binds to (set by Railway at deploy time) |

## Deploying to Railway

Create a service with this repo, set its root directory to `demo-railway/`,
and Railway will build `Dockerfile` and use `railway.toml`'s config. No
secrets are required.

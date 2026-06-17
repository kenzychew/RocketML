# ADR-0001: Model and serving approach

- Status: Accepted
- Date: 2026-06-16

## Context

RocketML is a serving platform; the model is the payload, not the focus. It
needs a text classifier that is small, fast on CPU, and deterministic, so CI
and the container stay light and reproducible. The serving image must stay
light: no GPU, no multi-GB artifacts.

## Decision

**Model.** A scikit-learn pipeline -- regex cleaning -> TF-IDF (1-2 grams, 20k
features) -> LogisticRegression -- trained on a 5k subset of the IMDB binary
sentiment dataset (negative/positive). It trains in seconds on CPU, the artifact
is under 1 MB, and `predict_proba` supplies the confidence score the
`{label, score}` contract needs. Holdout accuracy is ~0.86 / F1 ~0.87, which is
fine for a platform demo where the model is plumbing.

**Serving.** The app loads the fitted pipeline from a materialised joblib
artifact (config-driven `PRED_MODEL_PATH`) with no MLflow dependency at runtime.
Training still logs and registers the model to MLflow -- the registry is the
source of truth and lineage -- and `train.py` additionally writes the joblib
artifact that the image bakes in. Loading is lazy and cached, so `/health` does
not depend on the model being present.

## Consequences

- The serving image carries only FastAPI, uvicorn, scikit-learn, and a few small
  libraries -- no MLflow / Flask / SQLAlchemy server stack -- so it stays light.
- `docker run` is self-contained: the baked artifact lets the container predict
  with no external service.
- MLflow is a train-time concern only (tracking + registry), installed in the
  `train` dependency group and kept out of the serving runtime.
- Trade-off: serving does not pull a new model version live from the registry;
  promoting a model means re-running training and rebuilding the image. At this
  scale that is simpler and lighter than a registry client in the serving path.
  A live pull can be added later, once an MLflow service runs alongside serving.

## Alternatives considered

- **Full `mlflow` in the serving image, loading via `models:/...`.** Rejected:
  it pulls in Flask, SQLAlchemy, pandas and more, inflating the image for no
  serving benefit.
- **`mlflow-skinny` in the serving image.** Rejected: in MLflow 3.x
  `mlflow-skinny` is a metapackage that ships no importable `mlflow` module, so
  it cannot load a model on its own.
- **A transformer model (BERT/DistilBERT).** Rejected on image size and CPU
  latency; out of scope for a platform whose point is the pipeline, not the
  model.

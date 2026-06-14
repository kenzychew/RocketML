"""RocketML serving application.

Exposes the inference API:
    GET  /health   liveness / readiness probe
    POST /predict  text in, {label, score} out (stubbed in Phase 0)
    GET  /metrics  Prometheus metrics

The ``/predict`` response is a hardcoded stub for the Phase 0 walking skeleton;
the real model and MLflow integration arrive in Phase 1.
"""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app

from .schemas import PredictRequest, PredictResponse

app = FastAPI(title="RocketML", version="0.1.0")

# Expose Prometheus metrics for scraping at /metrics.
app.mount("/metrics", make_asgi_app())

PREDICT_REQUESTS = Counter("predict_requests", "Total number of /predict requests.")
PREDICT_LATENCY = Histogram("predict_latency_seconds", "Latency of /predict in seconds.")


@app.get("/health")
def health() -> dict[str, str]:
    """Report service liveness.

    Returns:
        A small status payload, ``{"status": "ok"}``.
    """
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Classify the input text.

    Phase 0 returns a hardcoded stub. Phase 1 will swap in the real model
    loaded from the MLflow registry.

    Args:
        request: Prediction request carrying the input text.

    Returns:
        The predicted label and its confidence score.
    """
    PREDICT_REQUESTS.inc()
    with PREDICT_LATENCY.time():
        # TODO(phase-1): replace the stub with the real model.predict(request.text).
        label, score = "positive", 0.97
    return PredictResponse(label=label, score=score)

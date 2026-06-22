"""RocketML serving application.

Exposes the inference API:
    GET  /health   liveness / readiness probe
    POST /predict  text in, {label, score} out (TF-IDF + LogReg sentiment model)
    GET  /metrics  Prometheus metrics

The model is loaded from a configured joblib artifact on first use; see
``model_loader`` and ``config``.
"""

import logging

from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, make_asgi_app

from . import model_loader
from .schemas import PredictRequest, PredictResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="RocketML", version="0.1.0")

# Expose Prometheus metrics for scraping at /metrics.
app.mount("/metrics", make_asgi_app())

PREDICT_REQUESTS = Counter("predict_requests", "Total number of /predict requests.")
PREDICT_ERRORS = Counter("predict_errors", "Total number of failed /predict requests.")
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
    """Classify the input text as positive/negative sentiment.

    Args:
        request: Prediction request carrying the input text.

    Returns:
        The predicted label and its confidence score.

    Raises:
        HTTPException: 503 if the model cannot be loaded or inference fails.
    """
    PREDICT_REQUESTS.inc()
    with PREDICT_LATENCY.time():
        try:
            label, score = model_loader.predict(request.text)
        except Exception as exc:
            PREDICT_ERRORS.inc()
            logger.exception("Prediction failed")
            raise HTTPException(status_code=503, detail="Model unavailable") from exc
    return PredictResponse(label=label, score=score)

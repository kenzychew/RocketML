"""FastAPI demo service for Railway.

Wraps the same sentiment pipeline serving/app runs (model loading and
/predict logic reused verbatim from serving/app, vendored into ./app -- see
app/__init__.py). Named main.py rather than app.py so it doesn't collide
with the app/ package it imports from.

The endpoint is public, so it carries the same two light guards demo/main.py
already solved for the Hugging Face Space: a per-client cooldown and a
global daily prediction cap ("demo credits"). Both counters are in-memory
and reset if the instance restarts, which is acceptable for a single-instance
demo.
"""

import logging
import os
import threading
import time
from datetime import UTC, date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from app import model_loader
from app.schemas import PredictRequest, PredictResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="RocketML Demo", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"

DAILY_CAP = int(os.environ.get("DEMO_DAILY_CAP", "200"))
COOLDOWN_SECONDS = float(os.environ.get("DEMO_COOLDOWN_SECONDS", "3.0"))

_lock = threading.Lock()
_day: date | None = None
_count = 0
_last_call: dict[str, float] = {}


def _client_id(request: Request) -> str:
    """Best-effort client identifier for throttling.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The originating client IP (first X-Forwarded-For hop behind
        Railway's proxy), or a placeholder when unavailable.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_limits(client: str) -> None:
    """Enforce the per-client cooldown and the global daily cap.

    Args:
        client: Client identifier from _client_id.

    Raises:
        HTTPException: 429 if the client is calling too fast or today's
            demo credits are spent.
    """
    global _day, _count
    with _lock:
        today = datetime.now(UTC).date()
        if _day != today:
            _day, _count = today, 0
            _last_call.clear()
        last = _last_call.get(client)
        now = time.monotonic()
        if last is not None and now - last < COOLDOWN_SECONDS:
            raise HTTPException(status_code=429, detail="One prediction every few seconds, please.")
        if _count >= DAILY_CAP:
            raise HTTPException(
                status_code=429, detail="Sorry, out of demo credits for now -- try again tomorrow."
            )
        _last_call[client] = now
        _count += 1


@app.get("/health")
def health() -> dict[str, str]:
    """Report service liveness.

    Returns:
        A small status payload, ``{"status": "ok"}``.
    """
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, http_request: Request) -> PredictResponse:
    """Classify the input text as positive/negative sentiment.

    Args:
        request: Prediction request carrying the input text.
        http_request: Injected by FastAPI; used for rate limiting.

    Returns:
        The predicted label and its confidence score.

    Raises:
        HTTPException: 429 if rate-limited, 503 if inference fails.
    """
    _check_limits(_client_id(http_request))
    try:
        label, score = model_loader.predict(request.text)
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=503, detail="Model unavailable") from exc
    return PredictResponse(label=label, score=score)


# Mounted last so it only catches paths /health and /predict didn't already match.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

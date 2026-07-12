"""Gradio demo for the RocketML sentiment model (Hugging Face Space).

The model is the same scikit-learn pipeline RocketML serves. Its TF-IDF step
references app.preprocessing.clean_text, so the app/ package ships alongside
this file for joblib.load to resolve.

The endpoint is public, so two light guards keep it from being hammered: a
per-client cooldown and a global daily prediction cap ("demo credits"). Both
counters are in-memory and reset if the instance restarts, which is acceptable
for a single-instance demo.
"""

import os
import threading
import time
from datetime import date, datetime, timezone

import spaces
import gradio as gr
import joblib

MODEL = joblib.load("sentiment.joblib")


@spaces.GPU
def _zerogpu_startup_probe() -> None:
    """Satisfy ZeroGPU's must-have-a-GPU-function startup check.

    The Space runs on zero-a10g hardware (the only free tier for new
    accounts), whose runtime refuses to start apps with no @spaces.GPU
    function. This one is registered but never called: inference is
    CPU-only and consumes no visitor GPU quota.
    """
    return None

DAILY_CAP = int(os.environ.get("DEMO_DAILY_CAP", "200"))
COOLDOWN_SECONDS = 3.0

EXAMPLES = [
    "An absolute masterpiece -- beautifully acted and deeply moving.",
    "Boring, predictable, and a complete waste of two hours.",
    "The plot dragged, but the soundtrack was wonderful.",
]

_lock = threading.Lock()
_day: date | None = None
_count = 0
_last_call: dict[str, float] = {}


def _client_id(request: gr.Request | None) -> str:
    """Best-effort client identifier for throttling.

    Args:
        request: The incoming Gradio request, if any.

    Returns:
        The originating client IP (first X-Forwarded-For hop behind the
        Cloud Run proxy), or a placeholder when unavailable.
    """
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_limits(client: str) -> None:
    """Enforce the per-client cooldown and the global daily cap.

    Args:
        client: Client identifier from _client_id.

    Raises:
        gr.Error: If the client is calling too fast or today's demo
            credits are spent.
    """
    global _day, _count
    with _lock:
        today = datetime.now(timezone.utc).date()
        if _day != today:
            _day, _count = today, 0
            _last_call.clear()
        last = _last_call.get(client)
        now = time.monotonic()
        if last is not None and now - last < COOLDOWN_SECONDS:
            raise gr.Error("One prediction every few seconds, please.")
        if _count >= DAILY_CAP:
            raise gr.Error("Sorry, out of demo credits for now -- try again tomorrow.")
        _last_call[client] = now
        _count += 1


def classify(text: str, request: gr.Request) -> dict[str, float]:
    """Return the model's class probabilities for the given text.

    Args:
        text: Raw review text from the UI.
        request: Injected by Gradio; used for rate limiting.

    Returns:
        Mapping of class label to probability, empty for blank input.
    """
    if not text or not text.strip():
        return {}
    _check_limits(_client_id(request))
    probs = MODEL.predict_proba([text])[0]
    return {str(label): float(p) for label, p in zip(MODEL.classes_, probs)}


demo = gr.Interface(
    fn=classify,
    inputs=gr.Textbox(lines=4, label="Text", placeholder="Type a movie review..."),
    outputs=gr.Label(num_top_classes=2, label="Sentiment"),
    title="RocketML -- sentiment demo",
    description=(
        "A TF-IDF + LogisticRegression sentiment classifier (trained on IMDB). "
        "This is the model served by the RocketML platform: "
        "https://github.com/kenzychew/RocketML -- the demo is lightly "
        "rate-limited and has a daily prediction budget."
    ),
    examples=EXAMPLES,
)

if __name__ == "__main__":
    # Host/port come from GRADIO_SERVER_NAME / GRADIO_SERVER_PORT, which the
    # hosting platform sets; forcing server_port here collides with the SSR
    # server on Spaces.
    demo.launch()

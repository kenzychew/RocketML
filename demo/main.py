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
from datetime import UTC, date, datetime

import gradio as gr
import joblib
import spaces

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
        today = datetime.now(UTC).date()
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
    return {str(label): float(p) for label, p in zip(MODEL.classes_, probs, strict=True)}


# Palette matches portfolio-hub's app/globals.css design tokens, so this Space
# reads as the same site as the rest of the portfolio's live demos. Every
# foreground/background pairing below was checked against WCAG AA before
# being chosen; keep pairings as-is rather than introducing new ones.
_BG = "#f6f1e7"  # --color-bg: page background
_BG_RAISED = "#efe8d9"  # --color-bg-raised: panel/card background
_FG = "#1c1917"  # --color-fg: body text
_FG_MUTED = "#5c564c"  # --color-fg-muted: secondary/muted text
_BORDER = "#ddd3bf"  # --color-border
_ACCENT = "#b8451f"  # --color-accent: buttons, sparing accent
_ACCENT_FG = "#f6f1e7"  # --color-accent-fg: text on the accent color
_ACCENT_INK = "#8a3216"  # --color-accent-ink: accent used as small/thin text

THEME = gr.themes.Base(
    font=[gr.themes.GoogleFont("Public Sans"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[
        gr.themes.GoogleFont("JetBrains Mono"),
        "ui-monospace",
        "Consolas",
        "monospace",
    ],
).set(
    body_background_fill=_BG,
    body_background_fill_dark=_BG,
    body_text_color=_FG,
    body_text_color_dark=_FG,
    body_text_color_subdued=_FG_MUTED,
    body_text_color_subdued_dark=_FG_MUTED,
    background_fill_primary=_BG,
    background_fill_primary_dark=_BG,
    background_fill_secondary=_BG_RAISED,
    background_fill_secondary_dark=_BG_RAISED,
    border_color_primary=_BORDER,
    border_color_primary_dark=_BORDER,
    border_color_accent=_ACCENT,
    border_color_accent_dark=_ACCENT,
    border_color_accent_subdued=_BORDER,
    border_color_accent_subdued_dark=_BORDER,
    color_accent=_ACCENT,
    color_accent_soft=_BG_RAISED,
    color_accent_soft_dark=_BG_RAISED,
    link_text_color=_ACCENT_INK,
    link_text_color_dark=_ACCENT_INK,
    link_text_color_hover=_ACCENT,
    link_text_color_hover_dark=_ACCENT,
    link_text_color_active=_ACCENT_INK,
    link_text_color_active_dark=_ACCENT_INK,
    link_text_color_visited=_ACCENT_INK,
    link_text_color_visited_dark=_ACCENT_INK,
    block_background_fill=_BG_RAISED,
    block_background_fill_dark=_BG_RAISED,
    block_border_color=_BORDER,
    block_border_color_dark=_BORDER,
    block_label_text_color=_FG_MUTED,
    block_label_text_color_dark=_FG_MUTED,
    block_label_border_color=_BORDER,
    block_label_border_color_dark=_BORDER,
    block_title_text_color=_FG,
    block_title_text_color_dark=_FG,
    panel_background_fill=_BG_RAISED,
    panel_background_fill_dark=_BG_RAISED,
    panel_border_color=_BORDER,
    panel_border_color_dark=_BORDER,
    input_background_fill=_BG,
    input_background_fill_dark=_BG,
    input_border_color=_BORDER,
    input_border_color_dark=_BORDER,
    input_placeholder_color=_FG_MUTED,
    input_placeholder_color_dark=_FG_MUTED,
    button_primary_background_fill=_ACCENT,
    button_primary_background_fill_dark=_ACCENT,
    button_primary_background_fill_hover=_ACCENT_INK,
    button_primary_background_fill_hover_dark=_ACCENT_INK,
    button_primary_text_color=_ACCENT_FG,
    button_primary_text_color_dark=_ACCENT_FG,
    button_primary_border_color=_ACCENT,
    button_primary_border_color_dark=_ACCENT,
    button_secondary_background_fill=_BG_RAISED,
    button_secondary_background_fill_dark=_BG_RAISED,
    button_secondary_background_fill_hover=_BORDER,
    button_secondary_background_fill_hover_dark=_BORDER,
    button_secondary_text_color=_FG,
    button_secondary_text_color_dark=_FG,
    button_secondary_border_color=_BORDER,
    button_secondary_border_color_dark=_BORDER,
    stat_background_fill=_ACCENT,
    stat_background_fill_dark=_ACCENT,
    loader_color=_ACCENT,
    loader_color_dark=_ACCENT,
    table_even_background_fill=_BG_RAISED,
    table_even_background_fill_dark=_BG_RAISED,
    table_odd_background_fill=_BG,
    table_odd_background_fill_dark=_BG,
    table_border_color=_BORDER,
    table_border_color_dark=_BORDER,
)

# Fraunces is loaded here (rather than as the theme's primary `font`) and
# scoped to the interface title only; Gradio's theme system has one body
# font slot, and the title renders as a plain inline-styled <h1>, not a
# themeable component.
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&display=swap');

.gradio-container h1 {
    font-family: 'Fraunces', ui-serif, serif;
}
"""

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
    theme=THEME,
    css=CUSTOM_CSS,
)

if __name__ == "__main__":
    # Host/port come from GRADIO_SERVER_NAME / GRADIO_SERVER_PORT, which the
    # hosting platform sets; forcing server_port here collides with the SSR
    # server on Spaces.
    demo.launch()

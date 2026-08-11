# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.
- The trained joblib artifact pickles a reference to `clean_text` by its training-time import path, `app.preprocessing` (see `model/train.py`'s `sys.path` trick). Any self-contained folder that loads the artifact directly (`demo/`, `demo-railway/`) must ship its own `app/preprocessing.py` at that exact module path, or `joblib.load` fails to unpickle the vectorizer's preprocessor. `serving/app/preprocessing.py` is the source of truth to copy from.
- Public-facing demo folders (`demo/`, `demo-railway/`) each bundle their own copy of `sentiment.joblib` rather than sharing one, since each is built as an independent, single-directory deploy root. Both artifacts are checked in as explicit exceptions to the root `.gitignore`'s `*.joblib` rule.
- Railway's build-plan step only reads a `railway.toml`/`railway.json` at the **repo root** — it never looks inside a service's configured root directory. The root `railway.json` (`{"builder": "dockerfile"}`) exists solely to force Dockerfile mode and skip Python auto-detection; the actual root directory and `dockerfilePath` for the `demo-railway` service are set at the Railway service level (dashboard/API), not in this repo.
- `demo/main.py`'s Gradio theme (`gr.themes.Base(...).set(...)`) mirrors portfolio-hub's `app/globals.css` warm palette so the HF Space reads as the same site as the other live demos. Gradio's theme system has one body font slot and one mono font slot, no separate heading slot — `gr.Interface`'s `title` renders as a bare inline-styled `<h1>`, not a themeable component, so a distinct heading font needs its own `@import` plus a scoped CSS rule via the `css=` param. HF Spaces README front matter's `colorFrom`/`colorTo` only accept `red, yellow, green, blue, indigo, purple, pink, gray` (no orange), so a rust/orange accent is approximated with `yellow`/`red`.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.

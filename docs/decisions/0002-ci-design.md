# ADR-0002: CI design

- Status: Accepted
- Date: 2026-06-17

## Context

Every push should be validated, and `main` should publish a deployable image.
The serving image bakes the model artifact, which is gitignored, so CI has to
produce it rather than read it from the repo.

## Decision

One workflow (`.github/workflows/ci.yml`) with two jobs:

- **`test`** -- on every push to `main` and every PR. `setup-uv` ->
  `uv sync --frozen` -> `ruff check` -> `pytest`. Fast feedback, pinned by
  `uv.lock`.
- **`build-and-push`** -- `needs: test`, main-only
  (`if: github.ref == 'refs/heads/main'`). Checkout -> `setup-uv` -> run
  `train.py` (the `train` group) to materialise `artifacts/sentiment.joblib` ->
  log in to GHCR with the built-in `GITHUB_TOKEN` -> build the serving image and
  push to `ghcr.io/<owner>/<repo>/serving`, tagged `:latest` and `:<sha>`.

Supporting choices:

- **Train in CI** instead of committing the model: keeps the binary out of git
  and the published image self-contained and reproducible (training is seeded).
- **Lowercase image name** (`${GITHUB_REPOSITORY,,}`): the repo is `RocketML`,
  but container registries require lowercase, so the tag is `.../rocketml/...`.
- **`GITHUB_TOKEN` with `packages: write`** (set on the job) -- no extra secrets.

## Consequences

- PRs run lint + test only; only `main` publishes.
- Each `main` build re-trains (~1-2 min: IMDB download + fit) -- acceptable and
  deterministic.
- GHCR packages are public (the repo is public).
- Pushing workflow files needs a token with the `workflow` scope
  (`gh auth refresh -h github.com -s workflow`).
- Re-training on every main push is wasteful; a later improvement is to train
  once, version the artifact, and decouple build from training.

## Alternatives considered

- **Commit the artifact:** simplest CI, but a binary model in git.
- **App-only image (model mounted at deploy):** lighter CI, but the published
  image is not self-contained.

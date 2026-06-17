"""Train and register the RocketML sentiment model.

Trains a TF-IDF + LogisticRegression pipeline on a subset of the IMDB movie
review dataset (binary sentiment), logs params/metrics/artifact to MLflow, and
registers it. It also writes a portable joblib artifact that the serving image
loads directly (serving carries no MLflow at runtime).

Run:
    uv run --group train python model/train.py

The MLflow tracking URI comes from MLFLOW_TRACKING_URI (defaults to a local
sqlite store). View the registry with:
    uv run --group train mlflow ui --backend-store-uri sqlite:///mlflow.db
"""

import logging
import os
import random
import sys
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from datasets import load_dataset
from mlflow import MlflowClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

# Single source of truth for text cleaning: reuse the serving app's preprocessor
# so training and inference clean text identically.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "serving"))
from app.preprocessing import clean_text  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rocketml.train")

SEED = 42
MODEL_NAME = "rocketml-sentiment"
EXPERIMENT_NAME = "rocketml-sentiment"
MODEL_ALIAS = "staging"
TRAIN_SAMPLES = 5000
TEST_SAMPLES = 5000
LABELS = ["negative", "positive"]  # IMDB label ids: 0 -> negative, 1 -> positive
ARTIFACT_PATH = Path("artifacts") / "sentiment.joblib"


def load_imdb_subset(
    n_train: int, n_test: int, seed: int
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Load a deterministic IMDB subset as (X_train, y_train, X_test, y_test).

    Args:
        n_train: Number of training reviews to sample.
        n_test: Number of test reviews to sample.
        seed: Shuffle seed for deterministic sampling.

    Returns:
        Raw review texts and "negative"/"positive" labels for train and test.
    """
    logger.info("Loading IMDB dataset from Hugging Face datasets")
    ds = load_dataset("stanfordnlp/imdb")
    train = ds["train"].shuffle(seed=seed).select(range(n_train))
    test = ds["test"].shuffle(seed=seed).select(range(n_test))
    y_train = [LABELS[int(label)] for label in train["label"]]
    y_test = [LABELS[int(label)] for label in test["label"]]
    return train["text"], y_train, test["text"], y_test


def build_pipeline() -> Pipeline:
    """Build the clean -> TF-IDF -> LogisticRegression pipeline."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    ngram_range=(1, 2),
                    max_features=20000,
                    min_df=5,
                    sublinear_tf=True,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, C=1.0, random_state=SEED)),
        ]
    )


def main() -> None:
    """Train, evaluate, log to MLflow, register, and materialise the artifact."""
    random.seed(SEED)

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info("MLflow tracking URI: %s", tracking_uri)

    x_train, y_train, x_test, y_test = load_imdb_subset(TRAIN_SAMPLES, TEST_SAMPLES, SEED)
    logger.info("Loaded %d train / %d test reviews", len(x_train), len(x_test))

    pipeline = build_pipeline()
    params = {
        "model": "tfidf+logreg",
        "ngram_range": "(1, 2)",
        "max_features": 20000,
        "min_df": 5,
        "C": 1.0,
        "train_samples": TRAIN_SAMPLES,
        "test_samples": TEST_SAMPLES,
        "seed": SEED,
    }

    with mlflow.start_run(run_name="tfidf-logreg") as run:
        mlflow.log_params(params)
        logger.info("Fitting pipeline on %d reviews", len(x_train))
        pipeline.fit(x_train, y_train)

        preds = pipeline.predict(x_test)
        accuracy = float(accuracy_score(y_test, preds))
        f1 = float(f1_score(y_test, preds, pos_label="positive"))
        logger.info("accuracy=%.4f  f1=%.4f", accuracy, f1)
        mlflow.log_metrics({"accuracy": accuracy, "f1": f1})

        mlflow.sklearn.log_model(
            pipeline,
            name="model",
            registered_model_name=MODEL_NAME,
        )
        logger.info("Logged and registered '%s' from run %s", MODEL_NAME, run.info.run_id)

    client = MlflowClient()
    latest = max(
        client.search_model_versions(f"name='{MODEL_NAME}'"),
        key=lambda v: int(v.version),
    )
    client.set_registered_model_alias(MODEL_NAME, MODEL_ALIAS, latest.version)
    logger.info("Set alias '%s' -> %s v%s", MODEL_ALIAS, MODEL_NAME, latest.version)

    # Materialise a portable artifact for the serving image to load directly
    # (serving uses joblib, not MLflow, so the image stays light).
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, ARTIFACT_PATH)
    logger.info("Saved serving artifact to %s", ARTIFACT_PATH)

    print(
        f"\nRegistered {MODEL_NAME} v{latest.version} (alias '{MODEL_ALIAS}')  "
        f"accuracy={accuracy:.4f}  f1={f1:.4f}\n"
        f"Serving artifact: {ARTIFACT_PATH}"
    )


if __name__ == "__main__":
    main()

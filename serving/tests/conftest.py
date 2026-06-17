"""Shared test fixtures.

Provides a tiny sentiment model saved to a temp joblib file so the API tests
run against the real load path without any network or MLflow server.
"""

import joblib
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app import config, model_loader
from app.preprocessing import clean_text

_POSITIVE = [
    "a wonderful brilliant and fantastic film, absolutely loved it",
    "superb excellent acting, a genuine masterpiece",
    "amazing delightful and the best movie i have seen",
]
_NEGATIVE = [
    "a terrible boring and awful waste of time",
    "dull, disappointing, and poorly made, hated it",
    "the worst film, horrible and painfully bad",
]


@pytest.fixture(scope="session", autouse=True)
def tiny_model(tmp_path_factory: pytest.TempPathFactory):
    """Train a tiny pipeline, save it to joblib, and point the app at it."""
    texts = _POSITIVE + _NEGATIVE
    labels = ["positive"] * len(_POSITIVE) + ["negative"] * len(_NEGATIVE)
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(preprocessor=clean_text)),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    pipeline.fit(texts, labels)

    model_path = tmp_path_factory.mktemp("model") / "sentiment.joblib"
    joblib.dump(pipeline, model_path)

    config.SETTINGS.pred_model_path = str(model_path)
    model_loader.load_model.cache_clear()
    yield
    model_loader.load_model.cache_clear()

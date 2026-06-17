"""Load the sentiment model: a joblib artifact, loaded once and cached.

MLflow handles tracking and the registry at train time; serving loads a
materialised artifact from a configured path, so the serving image carries no
MLflow dependency at runtime. Loading is lazy and cached, so /health stays up
even before the artifact is present.
"""

import logging
from functools import lru_cache

import joblib
from sklearn.pipeline import Pipeline

from .config import SETTINGS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_model() -> Pipeline:
    """Load and cache the sentiment pipeline from the configured path.

    Returns:
        The fitted scikit-learn pipeline (clean -> TF-IDF -> LogReg).
    """
    logger.info("Loading model from %s", SETTINGS.pred_model_path)
    model = joblib.load(SETTINGS.pred_model_path)
    logger.info("Model loaded (classes: %s)", list(model.classes_))
    return model


def predict(text: str) -> tuple[str, float]:
    """Classify text and return (label, confidence score in [0, 1]).

    Args:
        text: Raw input text.

    Returns:
        The predicted label and the model's confidence in that label.
    """
    model = load_model()
    label = str(model.predict([text])[0])
    score = float(model.predict_proba([text]).max())
    return label, score

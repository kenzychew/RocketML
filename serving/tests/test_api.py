"""API tests for the RocketML serving app.

These run against a tiny locally-saved model (see conftest.tiny_model), so they
need no MLflow server or network.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    """/health returns 200 with the ok status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_label_and_score() -> None:
    """/predict returns a well-formed {label, score}."""
    response = client.post("/predict", json={"text": "the cast was great"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"label", "score"}
    assert body["label"] in {"positive", "negative"}
    assert 0.0 <= body["score"] <= 1.0


def test_predict_positive() -> None:
    """A clearly positive review is classified positive."""
    response = client.post(
        "/predict",
        json={"text": "a wonderful, brilliant and fantastic film, loved it"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "positive"
    assert 0.5 < body["score"] <= 1.0


def test_predict_negative() -> None:
    """A clearly negative review is classified negative."""
    response = client.post(
        "/predict",
        json={"text": "a terrible, boring and awful waste of time"},
    )
    assert response.status_code == 200
    assert response.json()["label"] == "negative"

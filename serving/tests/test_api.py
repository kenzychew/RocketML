"""API tests for the RocketML serving app (Phase 0 stub)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    """/health returns 200 with the ok status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_label_and_score() -> None:
    """/predict accepts text and returns a well-formed {label, score}."""
    response = client.post(
        "/predict",
        json={"text": "shipping was fast and it works great"},
    )
    assert response.status_code == 200

    body = response.json()
    assert set(body) == {"label", "score"}
    assert isinstance(body["label"], str) and body["label"]
    assert 0.0 <= body["score"] <= 1.0

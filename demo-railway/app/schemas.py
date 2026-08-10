"""Pydantic request and response schemas for the RocketML inference API."""

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Request body for the ``/predict`` endpoint.

    Attributes:
        text: Raw input text to classify.
    """

    text: str = Field(..., description="Raw input text to classify.")


class PredictResponse(BaseModel):
    """Response body returned by the ``/predict`` endpoint.

    Attributes:
        label: Predicted class label.
        score: Confidence score for the prediction, in the range [0, 1].
    """

    label: str = Field(..., description="Predicted class label.")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score in [0, 1].")

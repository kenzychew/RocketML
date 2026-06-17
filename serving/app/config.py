"""Application settings for the RocketML serving app.

Env-driven (with optional .env), so the model location is never hardcoded: set
PRED_MODEL_PATH to wherever the serving artifact lives (a local path baked into
the image, or a mounted volume).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, read from the environment (or a local .env file)."""

    api_name: str = "RocketML"
    pred_model_path: str = "artifacts/sentiment.joblib"

    model_config = SettingsConfigDict(env_file=".env")


SETTINGS = Settings()

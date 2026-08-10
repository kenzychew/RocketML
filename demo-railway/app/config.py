"""Application settings for the Railway demo app.

Env-driven (with optional .env), so the model location is never hardcoded: set
PRED_MODEL_PATH to wherever the demo's bundled artifact lives. Mirrors
serving/app/config.py; only the default path differs (this folder bundles its
own copy of the artifact under model/, like demo/sentiment.joblib does).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, read from the environment (or a local .env file)."""

    api_name: str = "RocketML Demo"
    pred_model_path: str = "model/sentiment.joblib"

    model_config = SettingsConfigDict(env_file=".env")


SETTINGS = Settings()

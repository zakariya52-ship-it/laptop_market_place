"""Central backend configuration and resolved filesystem paths."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = (PROJECT_ROOT / ".env").resolve()


class Settings(BaseSettings):
    """Application settings loaded from the repository root .env file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000
    backend_url: str = "http://127.0.0.1:8000"
    model_path: Path = Field(
        default=Path("backend/artifacts/price_regressor.joblib"),
        validation_alias="MODEL_PATH",
    )
    api_v1_str: str = "/api/v1"
    project_name: str = "Laptop Price Predictor API"
    project_description: str = "Predict laptop prices from hardware specifications."
    project_version: str = "1.0.0"

    def _resolve_project_path(self, value: Path) -> Path:
        return (value if value.is_absolute() else PROJECT_ROOT / value).resolve()

    @property
    def MODEL_PATH(self) -> Path:
        """Return the configured model artifact as an absolute path."""
        return self._resolve_project_path(self.model_path)

    @property
    def API_V1_STR(self) -> str:
        return self.api_v1_str

    @property
    def PROJECT_NAME(self) -> str:
        return self.project_name

    @property
    def PROJECT_DESCRIPTION(self) -> str:
        return self.project_description

    @property
    def PROJECT_VERSION(self) -> str:
        return self.project_version


settings = Settings()
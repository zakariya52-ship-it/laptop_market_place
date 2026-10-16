"""Load pipeline paths from .env and ML settings from config.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = (PROJECT_ROOT / ".env").resolve()
load_dotenv(ENV_PATH)


def _required_env_path(key: str) -> Path:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    path = Path(value)
    return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()


RAW_DATA_PATH = _required_env_path("RAW_DATA_PATH")
PROCESSED_DATA_PATH = _required_env_path("PROCESSED_DATA_PATH")
MODEL_PATH = _required_env_path("MODEL_PATH")
METRICS_REPORT_PATH = _required_env_path("METRICS_REPORT_PATH")
CONFIG_YAML_PATH = _required_env_path("CONFIG_YAML_PATH")

with CONFIG_YAML_PATH.open("r", encoding="utf-8") as config_file:
    CONFIG: dict[str, Any] = yaml.safe_load(config_file)

if not isinstance(CONFIG, dict):
    raise RuntimeError(f"Expected a mapping in {CONFIG_YAML_PATH}")


def get_config(*keys: str) -> Any:
    """Return a nested config.yaml value using its exact key path."""
    value: Any = CONFIG
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise KeyError(f"Missing config key: {'.'.join(keys)}")
        value = value[key]
    return value

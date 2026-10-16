"""Pydantic schemas for laptop price prediction."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.schemas.known_values import (
    COMPANIES,
    CPUS,
    GPUS,
    OPERATING_SYSTEMS,
    SCREEN_RESOLUTIONS,
    STORAGE_CATEGORIES,
    STORAGE_TYPES,
    TYPE_NAMES,
)


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", "_", str(value).strip().lower())


def _known_value(field_name: str, allowed: frozenset[str]):
    def validate(value: Any) -> str:
        normalized = _normalize(value)
        if normalized not in allowed:
            raise ValueError(
                f"{field_name} must be a recognized value from the training data."
            )
        return normalized

    return validate


class LaptopPredictionInput(BaseModel):
    """Raw laptop features accepted by the prediction endpoint."""

    company: str = Field(..., min_length=1)
    type_name: str = Field(..., min_length=1, max_length=120)
    inches: float = Field(..., ge=7.0, le=18.0)
    screen_resolution: str = Field(..., min_length=1)
    cpu: str = Field(..., min_length=1, max_length=120)
    gpu: str = Field(..., min_length=1, max_length=120)
    os: str = Field(..., min_length=1)
    touch_screen: int = Field(..., ge=0, le=1)
    ips: int = Field(..., ge=0, le=1)
    x_res: int = Field(..., ge=800, le=4000)
    y_res: int = Field(..., ge=600, le=3000)
    ppi: float = Field(..., ge=84.89, le=323.45)
    dedicated_gpu: int = Field(..., ge=0, le=1)
    ram_gb: float = Field(..., ge=4.0, le=192.0)
    weight_kg: float = Field(..., ge=0.0, le=4.12)
    ssd: int = Field(..., ge=0, le=12000)
    hhd: int = Field(..., ge=0, le=128)
    storage_type: str = Field(..., min_length=1)
    total_storage_gb: float = Field(..., ge=32.0, le=12000.0)
    storage_category: str = Field(..., min_length=1)

    _validate_company = field_validator("company", mode="before")(
        _known_value("company", COMPANIES)
    )
    _validate_type_name = field_validator("type_name", mode="before")(
        _known_value("type_name", TYPE_NAMES)
    )
    _validate_screen_resolution = field_validator("screen_resolution", mode="before")(
        _known_value("screen_resolution", SCREEN_RESOLUTIONS)
    )
    _validate_cpu = field_validator("cpu", mode="before")(
        _known_value("cpu", CPUS)
    )
    _validate_gpu = field_validator("gpu", mode="before")(
        _known_value("gpu", GPUS)
    )
    _validate_os = field_validator("os", mode="before")(
        _known_value("os", OPERATING_SYSTEMS)
    )
    _validate_storage_type = field_validator("storage_type", mode="before")(
        _known_value("storage_type", STORAGE_TYPES)
    )
    _validate_storage_category = field_validator("storage_category", mode="before")(
        _known_value("storage_category", STORAGE_CATEGORIES)
    )

    @model_validator(mode="after")
    def validate_storage_total(self) -> "LaptopPredictionInput":
        actual_total = self.ssd + self.hhd
        if self.total_storage_gb != actual_total:
            raise ValueError(
                "total_storage_gb must equal ssd plus hhd for the supplied laptop."
            )
        return self


class LaptopPredictionOutput(BaseModel):
    """Prediction response returned by the API."""

    predicted_price: float
    currency: str = "USD"
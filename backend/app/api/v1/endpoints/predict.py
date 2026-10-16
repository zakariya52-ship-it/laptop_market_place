"""Laptop price prediction endpoint and model loading helpers."""

from __future__ import annotations

import re
import sys
import types
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from backend.app.core.config import settings
from backend.app.schemas.laptop import LaptopPredictionInput, LaptopPredictionOutput

router = APIRouter()

RAW_FEATURE_COLUMNS = [
    "Company",
    "TypeName",
    "Inches",
    "ScreenResolution",
    "Cpu",
    "Gpu",
    "OpSys",
    "TouchScreen",
    "Ips",
    "X_res",
    "Y_res",
    "ppi",
    "Dedicated_Gpu",
    "Ram_GB",
    "Weight_kg",
    "SSD",
    "HHD",
    "Storage_Type",
    "Total_Storage_GB",
    "Storage_Category",
]


def load_model() -> Any:
    """Load the configured serialized pipeline once during application startup."""
    model_path = Path(settings.MODEL_PATH).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"Model artifact not found at {model_path}")

    project_root = Path(__file__).resolve().parents[5]
    ml_pipeline_root = (project_root / "ml_pipeline").resolve()
    ml_pipeline_root_string = str(ml_pipeline_root)
    if ml_pipeline_root_string not in sys.path:
        sys.path.insert(0, ml_pipeline_root_string)

    # The existing artifact was serialized with the legacy ``src`` module name.
    # Keep compatibility aliases in memory without changing the project layout.
    import ml_pipeline.src.data_loader as data_loader
    import ml_pipeline.src.feature_engineering as feature_engineering

    legacy_src = sys.modules.setdefault("src", types.ModuleType("src"))
    legacy_src.__path__ = [ml_pipeline_root_string]
    sys.modules.setdefault("src.pipeline_features", feature_engineering)
    sys.modules.setdefault("src.utils", data_loader)
    return joblib.load(model_path)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "_", value.strip().lower())


def _input_to_dataframe(payload: LaptopPredictionInput) -> pd.DataFrame:
    record = {
        "Company": _normalize_text(payload.company),
        "TypeName": _normalize_text(payload.type_name),
        "Inches": payload.inches,
        "ScreenResolution": _normalize_text(payload.screen_resolution),
        "Cpu": _normalize_text(payload.cpu),
        "Gpu": _normalize_text(payload.gpu),
        "OpSys": _normalize_text(payload.os),
        "TouchScreen": payload.touch_screen,
        "Ips": payload.ips,
        "X_res": payload.x_res,
        "Y_res": payload.y_res,
        "ppi": payload.ppi,
        "Dedicated_Gpu": payload.dedicated_gpu,
        "Ram_GB": payload.ram_gb,
        "Weight_kg": payload.weight_kg,
        "SSD": payload.ssd,
        "HHD": payload.hhd,
        "Storage_Type": _normalize_text(payload.storage_type),
        "Total_Storage_GB": payload.total_storage_gb,
        "Storage_Category": _normalize_text(payload.storage_category),
    }
    return pd.DataFrame([record], columns=RAW_FEATURE_COLUMNS)


@router.post("/predict", response_model=LaptopPredictionOutput)
def predict_price(
    payload: LaptopPredictionInput,
    request: Request,
) -> LaptopPredictionOutput:
    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    try:
        prediction = float(model.predict(_input_to_dataframe(payload))[0])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    return LaptopPredictionOutput(predicted_price=round(max(prediction, 0.0), 2))
"""Evaluation helpers for trained laptop price pipelines."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

from ml_pipeline.src.config import METRICS_REPORT_PATH
from ml_pipeline.src.config import get_config

TARGET_COLUMN = get_config("cleaning", "target_column")


def evaluate_predictions(
    y_true: pd.Series,
    y_pred: object,
) -> dict[str, float]:
    """Return the metrics used by the original training workflow."""
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def evaluate_saved_pipeline(
    model_path: str | Path,
    features: pd.DataFrame,
    target: pd.Series,
) -> dict[str, float]:
    """Load a saved pipeline and evaluate it against a labelled frame."""
    resolved_model_path = Path(model_path).resolve()
    pipeline = joblib.load(resolved_model_path)
    predictions = pipeline.predict(features)
    return evaluate_predictions(target, predictions)


def save_metrics_report(
    metrics: dict[str, float],
    output_path: str | Path | None = None,
) -> Path:
    """Save metrics evaluation dictionary to a JSON report artifact using config settings."""
    report_path = Path(output_path).resolve() if output_path else METRICS_REPORT_PATH

    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics report successfully saved to: {report_path}")
    return report_path


__all__ = [
    "TARGET_COLUMN",
    "evaluate_predictions",
    "evaluate_saved_pipeline",
    "save_metrics_report",
]
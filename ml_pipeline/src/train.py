"""Train and persist the complete laptop price prediction pipeline."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ml_pipeline.src.config import MODEL_PATH, PROCESSED_DATA_PATH, get_config
from ml_pipeline.src.feature_engineering import (
    ColumnDropper,
    EnsureModelColumns,
    LaptopFeatureEngineer,
    NumericImputer,
    build_preprocessor,
)
from ml_pipeline.src.evaluate import evaluate_predictions, save_metrics_report

TARGET_COLUMN = get_config("cleaning", "target_column")
RAW_FEATURE_COLUMNS = get_config("features", "raw_feature_columns")


def _build_regressor(use_catboost: bool = True):
    model_config = get_config("model")
    if use_catboost and model_config["algorithm"] == "catboost":
        try:
            return CatBoostRegressor(**model_config["hyperparameters"])
        except Exception:
            pass

    fallback_config = model_config["fallback"]
    if fallback_config["algorithm"] != "random_forest":
        raise ValueError("Unsupported configured fallback algorithm")
    return RandomForestRegressor(**fallback_config["hyperparameters"])


def build_training_pipeline(use_catboost: bool = True) -> Pipeline:
    """Create the end-to-end sklearn pipeline."""
    return Pipeline(
        steps=[
            ("feature_engineer", LaptopFeatureEngineer()),
            ("drop_columns", ColumnDropper()),
            ("imputer", NumericImputer()),
            ("ensure_columns", EnsureModelColumns()),
            ("preprocessor", build_preprocessor()),
            ("regressor", _build_regressor(use_catboost=use_catboost)),
        ]
    )


def load_training_frame(
    processed_path: Path | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """Load processed data and split features from the target column."""
    resolved_path = (processed_path or PROCESSED_DATA_PATH).resolve()
    df = pd.read_csv(resolved_path)
    missing_features = [col for col in RAW_FEATURE_COLUMNS if col not in df.columns]
    if missing_features:
        raise ValueError(f"Processed dataset is missing required columns: {missing_features}")
    return df[RAW_FEATURE_COLUMNS], df[TARGET_COLUMN]


def train_and_save_pipeline(
    processed_path: Path | None = None,
    model_path: Path | None = None,
    test_size: float | None = None,
    random_state: int | None = None,
) -> Pipeline:
    """Fit the full pipeline, report metrics, and persist it to disk."""
    X, y = load_training_frame(processed_path)
    configured_test_size = (
        test_size if test_size is not None else get_config("model", "test_size")
    )
    configured_random_state = (
        random_state
        if random_state is not None
        else get_config("model", "random_state")
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=configured_test_size,
        random_state=configured_random_state,
    )

    pipeline = build_training_pipeline(
        use_catboost=get_config("model", "algorithm") == "catboost"
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    metrics = evaluate_predictions(y_test, y_pred)

    print("Training complete.")
    print(f"Test MAE : ${metrics['mae']:,.2f}")
    print(f"Test R²  : {metrics['r2']:.4f}")
    save_metrics_report(metrics)

    resolved_model_path = (model_path or MODEL_PATH).resolve()
    resolved_model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, resolved_model_path)
    print(f"Pipeline saved to: {resolved_model_path}")
    return pipeline


if __name__ == "__main__":
    from ml_pipeline.src.data_loader import run_data_pipeline

    run_data_pipeline()
    train_and_save_pipeline()

"""Feature engineering transformers for the laptop price pipeline."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml_pipeline.src.config import get_config

NUMERIC_FEATURES = get_config("features", "numerical_features")
CATEGORICAL_FEATURES = get_config("features", "categorical_features")
DROP_COLUMNS = get_config("features", "drop_columns")
_DERIVED_COLUMNS = get_config("features", "derived_columns")


class LaptopFeatureEngineer(BaseEstimator, TransformerMixin):
    """Create model-ready derived features from cleaned raw laptop records."""

    def fit(self, X: pd.DataFrame, y: object = None) -> "LaptopFeatureEngineer":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        df[_DERIVED_COLUMNS["gpu_brand"]] = df["Gpu"].apply(self._extract_gpu_brand)
        df[_DERIVED_COLUMNS["cpu_brand"]] = df["Cpu"].apply(self._extract_cpu_brand)
        df[_DERIVED_COLUMNS["storage_performance"]] = df["Storage_Category"].apply(
            self._extract_storage_performance
        )

        df[_DERIVED_COLUMNS["premium_tier"]] = (
            df["TypeName"]
            .str.contains(get_config("features", "premium_pattern"), case=False, regex=True)
            .astype(int)
        )
        df[_DERIVED_COLUMNS["ai_ready"]] = (
            df["TypeName"]
            .str.contains(get_config("features", "ai_ready_pattern"), case=False, regex=True)
            .astype(int)
        )
        word_count = get_config("features", "laptop_series_word_count")
        df[_DERIVED_COLUMNS["laptop_series"]] = (
            df["TypeName"].str.split().str[:word_count].str.join(" ")
        )
        return df

    @staticmethod
    def _extract_gpu_brand(gpu: object) -> str:
        text = str(gpu).lower()
        for brand, keyword in get_config("features", "gpu_brand_keywords").items():
            if keyword in text:
                return brand
        return "other"

    @staticmethod
    def _extract_cpu_brand(cpu: object) -> str:
        text = str(cpu).lower()
        match = re.search(
            get_config("features", "cpu_brand_pattern"),
            text,
            flags=re.IGNORECASE,
        )
        return match.group(1).replace(" ", "_") if match else "other"

    @staticmethod
    def _extract_storage_performance(category: object) -> str:
        text = str(category).lower()
        for performance, keyword in get_config(
            "features", "storage_performance_keywords"
        ).items():
            if keyword in text:
                return performance
        return "other"


class ColumnDropper(BaseEstimator, TransformerMixin):
    """Drop columns that should not reach the model preprocessor."""

    def __init__(self, columns: list[str] | None = None):
        self.columns = columns if columns is not None else DROP_COLUMNS

    def fit(self, X: pd.DataFrame, y: object = None) -> "ColumnDropper":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        existing = [col for col in self.columns if col in X.columns]
        return X.drop(columns=existing)


class NumericImputer(BaseEstimator, TransformerMixin):
    """Fill missing numeric values with medians learned during fitting."""

    def fit(self, X: pd.DataFrame, y: object = None) -> "NumericImputer":
        numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
        self.fill_values_ = X[numeric_cols].median(numeric_only=True).to_dict()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        for col, value in self.fill_values_.items():
            if col in df.columns:
                df[col] = df[col].fillna(value)
        return df


class EnsureModelColumns(BaseEstimator, TransformerMixin):
    """Guarantee all preprocessor columns exist before transformation."""

    def __init__(
        self,
        numeric_features: list[str] | None = None,
        categorical_features: list[str] | None = None,
    ):
        self.numeric_features = (
            numeric_features if numeric_features is not None else NUMERIC_FEATURES
        )
        self.categorical_features = (
            categorical_features
            if categorical_features is not None
            else CATEGORICAL_FEATURES
        )

    def fit(self, X: pd.DataFrame, y: object = None) -> "EnsureModelColumns":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        for col in self.numeric_features:
            if col not in df.columns:
                df[col] = 0
        for col in self.categorical_features:
            if col not in df.columns:
                df[col] = "unknown"
        return df


def build_preprocessor(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    """Build the ColumnTransformer used during training and inference."""
    numeric_features = numeric_features if numeric_features is not None else NUMERIC_FEATURES
    categorical_features = (
        categorical_features
        if categorical_features is not None
        else CATEGORICAL_FEATURES
    )
    if get_config("preprocessing", "scaler") != "standard":
        raise ValueError("Unsupported configured scaler")
    if get_config("preprocessing", "encoder") != "one_hot":
        raise ValueError("Unsupported configured encoder")
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            (
                "cat",
                OneHotEncoder(
                    handle_unknown=get_config(
                        "preprocessing", "encoder_handle_unknown"
                    ),
                    sparse_output=get_config(
                        "preprocessing", "encoder_sparse_output"
                    ),
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )

"""Load and clean the laptop dataset for offline model training."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from ml_pipeline.src.config import (
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    get_config,
)

TARGET_COLUMN = get_config("cleaning", "target_column")
_RAM_COLUMN_TOKEN = get_config("cleaning", "ram_column_token")
_STORAGE_COLUMN_TOKENS = tuple(get_config("cleaning", "storage_column_tokens"))
_EXCLUDED_STORAGE_COLUMNS = set(get_config("cleaning", "excluded_storage_columns"))
_STORAGE_PATTERN = get_config("parsing", "storage_pattern")
_RAM_PATTERN = get_config("parsing", "ram_pattern")
_DEFAULT_STORAGE_UNIT = get_config("parsing", "storage_default_unit")
_TB_UNIT = get_config("parsing", "storage_tb_unit")
_STORAGE_TB_MULTIPLIER = get_config("parsing", "storage_tb_multiplier")
_EMPTY_TEXT = get_config("parsing", "empty_text")
_UNKNOWN_TEXT = get_config("parsing", "unknown_text")
_WHITESPACE_PATTERN = get_config("parsing", "whitespace_pattern")
_WHITESPACE_REPLACEMENT = get_config("parsing", "text_whitespace_replacement")


def parse_storage_value(value: object) -> float | None:
    """Convert values like ``512GB`` or ``1 TB`` to gigabytes."""
    if value is None or (isinstance(value, float) and value != value):
        return None

    text = str(value).strip().lower().replace(",", "")
    if text == _EMPTY_TEXT:
        return None

    match = re.search(_STORAGE_PATTERN, text)
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2) or _DEFAULT_STORAGE_UNIT
    return amount * _STORAGE_TB_MULTIPLIER if unit == _TB_UNIT else amount


def parse_ram_value(value: object) -> float | None:
    """Convert RAM strings such as ``16GB RAM`` to numeric gigabytes."""
    if value is None or (isinstance(value, float) and value != value):
        return None

    text = str(value).strip().lower().replace(",", "")
    if text == _EMPTY_TEXT:
        return None

    match = re.search(_RAM_PATTERN, text)
    if match:
        return float(match.group(1))

    try:
        return float(text)
    except ValueError:
        return None


def normalize_text(value: object) -> str:
    """Normalize categorical text to a stable underscore-separated format."""
    if value is None or (isinstance(value, float) and value != value):
        return _UNKNOWN_TEXT

    return re.sub(
        _WHITESPACE_PATTERN,
        _WHITESPACE_REPLACEMENT,
        str(value).strip().lower(),
    )


def _coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ram_candidates = [col for col in df.columns if _RAM_COLUMN_TOKEN in col.lower()]
    storage_candidates = [
        col
        for col in df.columns
        if any(token in col.lower() for token in _STORAGE_COLUMN_TOKENS)
        and col.lower() not in _EXCLUDED_STORAGE_COLUMNS
    ]

    for col in ram_candidates:
        if df[col].dtype == object:
            df[col] = df[col].apply(parse_ram_value)

    for col in storage_candidates:
        if df[col].dtype == object:
            df[col] = df[col].apply(parse_storage_value)

    for col in df.select_dtypes(include=["number"]).columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _normalize_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].apply(normalize_text)
    return df


def _apply_winsorization(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    threshold = get_config("cleaning", "outlier_rate_threshold")
    iqr_multiplier = get_config("cleaning", "outlier_iqr_multiplier")
    lower_quantile = get_config("cleaning", "winsor_lower_quantile")
    upper_quantile = get_config("cleaning", "winsor_upper_quantile")
    for col in df.select_dtypes(include=np.number).columns:
        if col == TARGET_COLUMN:
            continue

        q1 = df[col].quantile(get_config("cleaning", "outlier_lower_quantile"))
        q3 = df[col].quantile(get_config("cleaning", "outlier_upper_quantile"))
        iqr = q3 - q1
        outlier_rate = (
            (df[col] < (q1 - iqr_multiplier * iqr))
            | (df[col] > (q3 + iqr_multiplier * iqr))
        ).mean()
        if outlier_rate > threshold:
            lower = df[col].quantile(lower_quantile)
            upper = df[col].quantile(upper_quantile)
            df[f"{col}__winsor"] = df[col].clip(lower, upper)

    return df


def clean_laptop_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the existing cleaning workflow to raw laptop records."""
    df = df.copy()
    index_columns = get_config("cleaning", "index_columns")
    existing_index_columns = [column for column in index_columns if column in df.columns]
    if existing_index_columns:
        df = df.drop(columns=existing_index_columns)

    df = _coerce_numeric_columns(df)
    df = df.dropna(subset=[TARGET_COLUMN]).drop_duplicates()

    storage_category_column = get_config("cleaning", "storage_category_column")
    if storage_category_column in df.columns:
        storage_category = df[storage_category_column].astype(str).str.strip().str.lower()
        excluded_categories = get_config("cleaning", "excluded_storage_categories")
        df = df[~storage_category.isin(excluded_categories)]

    df = _normalize_categorical_columns(df)
    return _apply_winsorization(df).reset_index(drop=True)


def run_data_pipeline(
    raw_path: str | Path | None = None,
    processed_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load, clean, and persist the processed dataset."""
    input_path = Path(raw_path).resolve() if raw_path else RAW_DATA_PATH
    output_path = Path(processed_path).resolve() if processed_path else PROCESSED_DATA_PATH

    df_clean = clean_laptop_data(pd.read_csv(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    return df_clean

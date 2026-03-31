"""
Data quality checks and cleaning
"""
from dataclasses import dataclass, field
from typing import List, Dict
import pandas as pd
import numpy as np


@dataclass
class QualityIssue:
    level: str   # 'error' | 'warning' | 'info'
    message: str


def check_quality(df: pd.DataFrame) -> List[QualityIssue]:
    """Return list of quality issues found in the dataframe."""
    issues = []

    # Missing values
    missing = df.isnull().sum()
    for col, count in missing[missing > 0].items():
        pct = count / len(df) * 100
        level = 'error' if pct > 30 else 'warning'
        issues.append(QualityIssue(level, f"«{col}»: {count} пропусков ({pct:.1f}%)"))

    # Duplicates
    dupes = df.duplicated().sum()
    if dupes > 0:
        issues.append(QualityIssue('warning', f"{dupes} дублирующихся строк (будут удалены при очистке)"))

    # Rows count
    if len(df) < 5:
        issues.append(QualityIssue('warning', f"Мало данных: {len(df)} строк — анализ может быть неточным"))

    return issues


def clean_data(df: pd.DataFrame, col_map: Dict[str, str]) -> pd.DataFrame:
    """
    Apply column mapping, parse types, remove duplicates.
    col_map: {original_col → standard_field}
    """
    df = df.copy()

    # Rename to standard names
    rename = {orig: std for orig, std in col_map.items() if orig in df.columns}
    df = df.rename(columns=rename)

    # Parse dates
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True)
        bad_dates = df['date'].isna().sum()
        if bad_dates > 0 and bad_dates < len(df):
            df = df.dropna(subset=['date'])

    # Parse numeric columns — handle Russian number formatting (spaces, commas)
    numeric_cols = ['impressions', 'clicks', 'TotalSum', 'ctr', 'cpm', 'cpc',
                    'viewability', 'vtr', 'frequency', 'reach', 'views']
    for col in numeric_cols:
        if col in df.columns:
            cleaned = (
                df[col].astype(str)
                .str.replace('\xa0', '', regex=False)
                .str.replace(' ', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.replace('%', '', regex=False)
            )
            df[col] = pd.to_numeric(cleaned, errors='coerce').fillna(0)
            # Ratio metrics stored as percent (e.g. 48.3 instead of 0.483) — normalize if > 1
            if col in ('ctr', 'viewability', 'vtr') and df[col].max() > 1:
                df[col] = df[col] / 100

    # Remove full duplicates
    df = df.drop_duplicates()

    # Standardize string columns
    for col in ['advertiser', 'campaign', 'format', 'banner_size', 'product']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

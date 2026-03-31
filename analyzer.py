"""
Metrics computation and aggregation
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

import config


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived metrics: CTR, CPM, CPC."""
    df = df.copy()
    imp = df.get('impressions', pd.Series(dtype=float))
    clk = df.get('clicks', pd.Series(dtype=float))
    spd = df.get('TotalSum', pd.Series(dtype=float))

    if 'clicks' in df.columns and 'impressions' in df.columns:
        df['ctr'] = np.where(imp > 0, clk / imp, 0)
    if 'TotalSum' in df.columns and 'impressions' in df.columns:
        df['cpm'] = np.where(imp > 0, spd / imp * 1000, 0)
    if 'TotalSum' in df.columns and 'clicks' in df.columns:
        df['cpc'] = np.where(clk > 0, spd / clk, 0)
    return df


def aggregate(df: pd.DataFrame, group_by: List[str]) -> pd.DataFrame:
    """Aggregate metrics by group_by columns with weighted averages for ratios."""
    if df.empty or not group_by:
        return df

    # Only group by columns that exist
    group_by = [c for c in group_by if c in df.columns]
    if not group_by:
        return df

    df = df.copy()
    sum_cols = [c for c in ['impressions', 'clicks', 'TotalSum',
                             'post_click_conversions', 'post_view_conversions', 'revenue']
                if c in df.columns]
    agg = {c: 'sum' for c in sum_cols}

    # Weighted average for ratio metrics
    weighted = ['viewability', 'vtr', 'frequency']
    for m in weighted:
        if m in df.columns and 'impressions' in df.columns:
            df[f'_w_{m}'] = df[m] * df['impressions']
            agg[f'_w_{m}'] = 'sum'

    result = df.groupby(group_by, as_index=False, observed=True).agg(agg)

    for m in weighted:
        if f'_w_{m}' in result.columns:
            result[m] = np.where(
                result['impressions'] > 0,
                result[f'_w_{m}'] / result['impressions'],
                0,
            )
            result = result.drop(columns=[f'_w_{m}'])

    return compute_metrics(result)


def summary(df: pd.DataFrame) -> Dict:
    """Compute top-level KPI summary."""
    imp = df['impressions'].sum() if 'impressions' in df.columns else 0
    clk = df['clicks'].sum() if 'clicks' in df.columns else 0
    spd = df['TotalSum'].sum() if 'TotalSum' in df.columns else 0
    return {
        'spend':       spd,
        'impressions': imp,
        'clicks':      clk,
        'ctr':         clk / imp if imp > 0 else 0,
        'cpm':         spd / imp * 1000 if imp > 0 else 0,
        'cpc':         spd / clk if clk > 0 else 0,
    }


def top_n(df: pd.DataFrame, group_col: str, metric: str = 'ctr', n: int = 10,
          min_impressions: int = None) -> pd.DataFrame:
    """Top-N by metric for a given dimension."""
    if group_col not in df.columns or metric not in df.columns:
        return pd.DataFrame()
    agg_df = aggregate(df, [group_col])
    if min_impressions and 'impressions' in agg_df.columns:
        agg_df = agg_df[agg_df['impressions'] >= (min_impressions or config.MIN_IMPRESSIONS)]
    return agg_df.nlargest(n, metric)


def anomalies(df: pd.DataFrame, metric: str = 'ctr', std_threshold: float = 2.0) -> pd.DataFrame:
    """Return rows where metric deviates by more than std_threshold standard deviations."""
    if metric not in df.columns or len(df) < 5:
        return pd.DataFrame()
    mean, std = df[metric].mean(), df[metric].std()
    if std == 0:
        return pd.DataFrame()
    df = df.copy()
    df['z_score'] = (df[metric] - mean) / std
    return df[df['z_score'].abs() > std_threshold].sort_values('z_score', ascending=False)

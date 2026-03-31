"""
Plotly chart generators
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Optional

from config import BRAND_COLORS, PLOTLY_TEMPLATE

CHART_HEIGHT = 420
CHART_HEIGHT_TALL = 480
FONT_FAMILY = "Inter, Arial, sans-serif"


def _base_layout(**kwargs) -> dict:
    h = kwargs.pop('height', CHART_HEIGHT)
    margin = kwargs.pop('margin', dict(l=16, r=16, t=48, b=16))
    return dict(
        template=PLOTLY_TEMPLATE,
        height=h,
        font=dict(family=FONT_FAMILY, size=13),
        title_font=dict(family=FONT_FAMILY, size=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=margin,
        **kwargs,
    )


def _pct_colors(values: pd.Series, base_color: str = "#4F46E5") -> list:
    n = len(values)
    if n <= len(BRAND_COLORS):
        return BRAND_COLORS[:n]
    return px.colors.sample_colorscale("Viridis", [i / n for i in range(n)])


def fmt_number(val: float) -> str:
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val/1_000:.1f}K"
    return f"{val:,.0f}"


def _truncate_label(label: str, max_len: int = 22) -> str:
    s = str(label)
    return s if len(s) <= max_len else s[:max_len] + '…'


def bar_comparison(df: pd.DataFrame, x_col: str, metrics: List[str],
                   title: str = '',
                   benchmarks: Optional[dict] = None) -> go.Figure:
    """Side-by-side bar charts for multiple metrics. benchmarks: {metric_label: value}"""
    metrics = [m for m in metrics if m in df.columns]
    if not metrics or df.empty:
        return go.Figure()
    fig = make_subplots(rows=1, cols=len(metrics),
                        subplot_titles=[m.upper() for m in metrics])
    for i, metric in enumerate(metrics, 1):
        colors = _pct_colors(df[metric])
        fig.add_trace(
            go.Bar(
                x=df[x_col], y=df[metric],
                marker_color=colors[:len(df)] if len(colors) >= len(df) else BRAND_COLORS[i % len(BRAND_COLORS)],
                name=metric, showlegend=False,
                hovertemplate=f"%{{x}}<br>{metric.upper()}: %{{y:,.2f}}<extra></extra>",
            ),
            row=1, col=i,
        )
        if benchmarks and metric in benchmarks:
            fig.add_hline(
                y=benchmarks[metric], line_dash='dash', line_color='#DC2626',
                annotation_text=f"норма {benchmarks[metric]}", annotation_font_size=10,
                row=1, col=i,
            )
    fig.update_layout(**_base_layout(title=title, showlegend=False))
    return fig


def dynamics_line(df: pd.DataFrame, x_col: str, metrics: List[str],
                  color_by: Optional[str] = None, title: str = '',
                  benchmarks: Optional[List[tuple]] = None) -> go.Figure:
    """Line chart. benchmarks: list of (label, value, color)"""
    fig = go.Figure()
    metrics = [m for m in metrics if m in df.columns]
    if not metrics or df.empty:
        return fig

    if color_by and color_by in df.columns:
        groups = df[color_by].dropna().unique()
        for i, grp in enumerate(groups):
            sub = df[df[color_by] == grp]
            for metric in metrics:
                fig.add_trace(go.Scatter(
                    x=sub[x_col], y=sub[metric], mode='lines+markers',
                    name=f"{grp} — {metric.upper()}",
                    line=dict(color=BRAND_COLORS[i % len(BRAND_COLORS)], width=2),
                    marker=dict(size=5),
                    hovertemplate=f"{grp}<br>{metric.upper()}: %{{y:,.3f}}<extra></extra>",
                ))
    else:
        for i, metric in enumerate(metrics):
            fig.add_trace(go.Scatter(
                x=df[x_col], y=df[metric], mode='lines+markers',
                name=metric.upper(),
                line=dict(color=BRAND_COLORS[i % len(BRAND_COLORS)], width=2),
                marker=dict(size=5),
                hovertemplate=f"{metric.upper()}: %{{y:,.3f}}<extra></extra>",
            ))

    if benchmarks:
        for label, value, color in benchmarks:
            fig.add_hline(
                y=value, line_dash='dot', line_color=color, line_width=1.5,
                annotation_text=label, annotation_position='top right',
                annotation_font_size=10, annotation_font_color=color,
            )

    fig.update_layout(**_base_layout(
        title=title, hovermode='x unified', height=CHART_HEIGHT_TALL,
        xaxis_title=None, yaxis_title=None,
        legend=dict(orientation='h', y=-0.15, x=0, font=dict(size=11)),
    ))
    return fig


def pie_chart(df: pd.DataFrame, label_col: str, value_col: str,
              title: str = '', selected_label: str = None) -> go.Figure:
    """Donut pie chart with optional pulled slice."""
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        return go.Figure()
    n = len(df)
    textinfo = 'percent' if n > 5 else 'label+percent'
    colors = _pct_colors(df[value_col])
    pull = [0.1 if str(row) == str(selected_label) and selected_label else 0
            for row in df[label_col]]
    truncated_labels = df[label_col].apply(_truncate_label)
    fig = go.Figure(go.Pie(
        labels=truncated_labels, values=df[value_col], hole=0.42,
        customdata=df[label_col],
        hovertemplate='%{customdata}<br>%{value:,.1f}<br>%{percent}<extra></extra>',
        marker=dict(colors=colors),
        textinfo=textinfo,
        textposition='inside',
        textfont=dict(size=11),
        pull=pull,
    ))
    fig.update_layout(**_base_layout(
        title=title,
        legend=dict(orientation='v', x=1.02, y=0.5, xanchor='left', yanchor='middle',
                    font=dict(size=11)),
        margin=dict(l=16, r=170, t=48, b=16),
    ))
    return fig


def treemap_chart(df: pd.DataFrame, label_col: str, value_col: str,
                  title: str = '') -> go.Figure:
    """Treemap for budget/metric distribution — better than pie for many items."""
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        return go.Figure()
    df = df.copy()
    df['_label'] = df[label_col].apply(_truncate_label)
    df['_pct'] = df[value_col] / df[value_col].sum() * 100
    fig = px.treemap(
        df, path=['_label'], values=value_col,
        color=value_col, color_continuous_scale='Blues',
        hover_data={value_col: ':,.1f', '_pct': ':.1f'},
        title=title,
    )
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>%{value:,.1f}<br>%{percentRoot:.1%}<extra></extra>',
        textinfo='label+percent root',
        textfont=dict(size=12),
    )
    fig.update_layout(**_base_layout(title=title, height=CHART_HEIGHT,
                                     coloraxis_showscale=False))
    return fig


def scatter_plot(df: pd.DataFrame, x: str, y: str,
                 size: Optional[str] = None, color: Optional[str] = None,
                 title: str = '', x_label: str = '', y_label: str = '') -> go.Figure:
    if df.empty or x not in df.columns or y not in df.columns:
        return go.Figure()
    kwargs = {
        'x': x, 'y': y, 'title': title,
        'color_discrete_sequence': BRAND_COLORS,
        'hover_name': color if color and color in df.columns else None,
    }
    if size and size in df.columns and pd.api.types.is_numeric_dtype(df[size]):
        kwargs['size'] = size
        kwargs['size_max'] = 40
    if color and color in df.columns:
        kwargs['color'] = color
    fig = px.scatter(df, **kwargs)
    # Per-trace hover: show name + coordinates. <extra></extra> hides the secondary box.
    x_lbl = x_label or x
    y_lbl = y_label or y
    fig.update_traces(
        hovertemplate=f"<b>%{{hovertext}}</b><br>{x_lbl}: %{{x:,.1f}}<br>{y_lbl}: %{{y:.2f}}<extra></extra>",
    )
    fig.update_layout(
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        legend=dict(
            title_text='',
            orientation='v',
            itemclick='toggleothers',
            itemdoubleclick='toggle',
        ),
        **_base_layout(height=CHART_HEIGHT_TALL),
    )
    return fig


def horizontal_bar(df: pd.DataFrame, y_col: str, x_col: str,
                   color_col: Optional[str] = None, title: str = '') -> go.Figure:
    if df.empty:
        return go.Figure()
    h = max(350, len(df) * 30)
    if color_col and color_col in df.columns:
        fig = px.bar(df, y=y_col, x=x_col, color=color_col, orientation='h',
                     title=title, color_discrete_sequence=BRAND_COLORS)
    else:
        fig = px.bar(df, y=y_col, x=x_col, orientation='h', title=title,
                     color_discrete_sequence=BRAND_COLORS)
    fig.update_traces(hovertemplate=f"%{{y}}<br>{x_col}: %{{x:,.1f}}<extra></extra>")
    fig.update_layout(**_base_layout(height=h))
    return fig


def funnel_chart(df: pd.DataFrame) -> go.Figure:
    stages, values = [], []
    for col, label in [('impressions', 'Показы'), ('clicks', 'Клики'),
                       ('post_click_conversions', 'Конверсии'), ('revenue', 'Доход')]:
        if col in df.columns and df[col].sum() > 0:
            stages.append(label)
            values.append(df[col].sum())
    if len(stages) < 2:
        return go.Figure()
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo='value+percent initial',
        textfont=dict(size=12),
        marker=dict(color=BRAND_COLORS[:len(stages)]),
    ))
    fig.update_layout(**_base_layout(title='Воронка конверсий'))
    return fig

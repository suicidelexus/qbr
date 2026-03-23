"""
Visualization Layer - генерация графиков
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional
import config


class ChartGenerator:
    """Генератор графиков"""
    
    def __init__(self, style: str = 'plotly'):
        self.style = style  # 'plotly' или 'matplotlib'
        self.colors = config.CHART_COLORS
    
    def advertiser_comparison(self, df: pd.DataFrame, metrics: List[str] = None) -> go.Figure:
        """Сравнение advertisers"""
        metrics = metrics or ['ctr', 'viewability', 'cpm']
        
        # Определяем колонку с advertiser
        adv_col = next((c for c in ('advertiser', 'advertiser_id', 'advertiser_source') if c in df.columns), None)
        if adv_col is None:
            return go.Figure()
        
        fig = make_subplots(
            rows=1, cols=len(metrics),
            subplot_titles=[m.upper() for m in metrics]
        )
        
        for i, metric in enumerate(metrics, 1):
            if metric in df.columns:
                fig.add_trace(
                    go.Bar(
                        x=df[adv_col],
                        y=df[metric],
                        name=metric.upper(),
                        marker_color=self.colors[i-1]
                    ),
                    row=1, col=i
                )
        
        fig.update_layout(
            title="Сравнение Advertisers",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def media_split_pie(self, df: pd.DataFrame, dimension: str = 'format') -> go.Figure:
        """Pie chart медиасплита"""
        if dimension not in df.columns or 'TotalSum' not in df.columns:
            return go.Figure()
        
        fig = go.Figure(data=[go.Pie(
            labels=df[dimension],
            values=df['TotalSum'],
            hole=0.3,
            marker=dict(colors=self.colors)
        )])
        
        fig.update_layout(
            title=f"Распределение бюджета по {dimension}",
            height=400
        )
        
        return fig
    
    def dynamics_line(self, df: pd.DataFrame, metrics: List[str] = None,
                      color_by: str = None) -> go.Figure:
        """Line chart динамики. color_by='advertiser' — отдельная линия на каждого."""
        metrics = metrics or ['ctr', 'cpm']
        
        if 'period' not in df.columns:
            return go.Figure()
        
        fig = go.Figure()

        if color_by and color_by in df.columns:
            groups = df[color_by].unique()
            for metric in metrics:
                if metric not in df.columns:
                    continue
                for grp in groups:
                    sub = df[df[color_by] == grp]
                    fig.add_trace(go.Scatter(
                        x=sub['period'],
                        y=sub[metric],
                        mode='lines+markers',
                        name=f"{grp} — {metric.upper()}"
                    ))
        else:
            for metric in metrics:
                if metric in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['period'],
                        y=df[metric],
                        mode='lines+markers',
                        name=metric.upper()
                    ))
        
        fig.update_layout(
            title="Динамика метрик",
            xaxis_title="Период",
            yaxis_title="Значение",
            height=500,
            hovermode='x unified'
        )
        
        return fig

    def banner_size_chart(self, df: pd.DataFrame, adv_col: str = 'advertiser') -> go.Figure:
        """Горизонтальный bar chart по banner_size в разрезе advertiser"""
        if df.empty or 'banner_size' not in df.columns:
            return go.Figure()

        metric = 'impressions' if 'impressions' in df.columns else 'TotalSum'
        if metric not in df.columns:
            return go.Figure()

        if adv_col and adv_col in df.columns:
            fig = px.bar(
                df, y='banner_size', x=metric, color=adv_col,
                orientation='h', barmode='group',
                title='Распределение по BannerSize (display)',
                height=max(400, len(df) * 22),
            )
        else:
            fig = px.bar(
                df, y='banner_size', x=metric,
                orientation='h',
                title='Распределение по BannerSize (display)',
                height=max(400, len(df) * 22),
            )

        fig.update_layout(yaxis_title='Banner Size', xaxis_title=metric.capitalize())
        return fig
    
    def frequency_scatter(self, df: pd.DataFrame) -> go.Figure:
        """Scatter: frequency vs CTR"""
        if 'frequency' not in df.columns or 'ctr' not in df.columns:
            return go.Figure()
        
        fig = px.scatter(
            df,
            x='frequency',
            y='ctr',
            size='impressions' if 'impressions' in df.columns else None,
            color='advertiser' if 'advertiser' in df.columns else None,
            title="Зависимость CTR от Frequency",
            labels={'frequency': 'Frequency', 'ctr': 'CTR'}
        )
        
        fig.update_layout(height=400)
        
        return fig
    
    def format_performance(self, df: pd.DataFrame) -> go.Figure:
        """Stacked bar: performance by format"""
        if 'format' not in df.columns:
            return go.Figure()
        
        metrics = ['impressions', 'clicks']
        
        fig = go.Figure()
        
        for metric in metrics:
            if metric in df.columns:
                fig.add_trace(go.Bar(
                    x=df['format'],
                    y=df[metric],
                    name=metric.upper()
                ))
        
        fig.update_layout(
            title="Performance по форматам",
            barmode='group',
            height=400
        )
        
        return fig
    
    def dmp_comparison(self, data: dict) -> go.Figure:
        """Сравнение с DMP и без DMP"""
        if not data.get('with_dmp') or not data.get('without_dmp'):
            return go.Figure()
        
        metrics = ['ctr', 'viewability', 'cpm']
        
        with_dmp = data['with_dmp']
        without_dmp = data['without_dmp']
        
        fig = go.Figure()
        
        x = ['С DMP', 'Без DMP']
        
        for metric in metrics:
            if metric in with_dmp and metric in without_dmp:
                fig.add_trace(go.Bar(
                    x=x,
                    y=[with_dmp[metric], without_dmp[metric]],
                    name=metric.upper()
                ))
        
        fig.update_layout(
            title="Сравнение эффективности: DMP vs Без DMP",
            barmode='group',
            height=400
        )
        
        return fig
    
    def save_figure(self, fig: go.Figure, filename: str, format: str = 'html'):
        """Сохранение графика"""
        if format == 'html':
            fig.write_html(filename)
        elif format == 'png':
            fig.write_image(filename)
        elif format == 'pdf':
            fig.write_image(filename)
    
    def generate_all_charts(self, analysis_results: dict, output_dir: str = './charts'):
        """Генерация всех графиков из результатов анализа"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        charts = {}
        
        # Advertiser comparison
        if not analysis_results['advertisers']['data'].empty:
            fig = self.advertiser_comparison(analysis_results['advertisers']['data'])
            self.save_figure(fig, f'{output_dir}/advertisers.html')
            charts['advertisers'] = fig
        
        # Media split
        if not analysis_results['media_split']['data'].empty:
            fig = self.media_split_pie(analysis_results['media_split']['data'])
            self.save_figure(fig, f'{output_dir}/media_split.html')
            charts['media_split'] = fig
        
        # Dynamics
        if not analysis_results['dynamics']['data'].empty:
            fig = self.dynamics_line(analysis_results['dynamics']['data'])
            self.save_figure(fig, f'{output_dir}/dynamics.html')
            charts['dynamics'] = fig
        
        # DMP
        if analysis_results['dmp']['data']:
            fig = self.dmp_comparison(analysis_results['dmp']['data'])
            self.save_figure(fig, f'{output_dir}/dmp.html')
            charts['dmp'] = fig
        
        # Correlation heatmap
        if 'correlation' in analysis_results and not analysis_results['correlation']['data'].empty:
            fig = self.correlation_heatmap(analysis_results['correlation']['data'])
            self.save_figure(fig, f'{output_dir}/correlation.html')
            charts['correlation'] = fig
        
        # Budget optimization
        if 'budget_optimization' in analysis_results and analysis_results['budget_optimization']['data']:
            fig = self.budget_optimization_chart(analysis_results['budget_optimization']['data'])
            self.save_figure(fig, f'{output_dir}/budget_optimization.html')
            charts['budget_optimization'] = fig
        
        return charts
    
    def correlation_heatmap(self, correlation_df: pd.DataFrame) -> go.Figure:
        """Тепловая карта корреляций"""
        if correlation_df.empty:
            return go.Figure()
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_df.values,
            x=correlation_df.columns,
            y=correlation_df.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_df.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Корреляция метрик",
            height=500,
            xaxis_title="Метрики",
            yaxis_title="Метрики"
        )
        
        return fig
    
    def budget_optimization_chart(self, data: dict) -> go.Figure:
        """Визуализация оптимизации бюджета"""
        if not data or not data.get('underperformers'):
            return go.Figure()
        
        # Данные underperformers и overperformers
        underperformers = pd.DataFrame(data['underperformers'])
        overperformers = pd.DataFrame(data.get('overperformers', []))
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Underperformers', 'Overperformers'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Underperformers
        if not underperformers.empty:
            fig.add_trace(
                go.Bar(
                    x=underperformers['advertiser'],
                    y=underperformers['TotalSum'],
                    name='Budget',
                    marker_color='red',
                    text=underperformers['ctr'].apply(lambda x: f'{x:.2%}'),
                    textposition='auto'
                ),
                row=1, col=1
            )
        
        # Overperformers
        if not overperformers.empty:
            fig.add_trace(
                go.Bar(
                    x=overperformers['advertiser'],
                    y=overperformers['TotalSum'],
                    name='Budget',
                    marker_color='green',
                    text=overperformers['ctr'].apply(lambda x: f'{x:.2%}'),
                    textposition='auto'
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title=f"Оптимизация бюджета (потенциальная экономия: {data.get('potential_savings', 0):,.0f})",
            height=500,
            showlegend=False
        )
        
        return fig
    
    def performance_funnel(self, df: pd.DataFrame) -> go.Figure:
        """Воронка эффективности"""
        if df.empty or 'impressions' not in df.columns:
            return go.Figure()
        
        # Считаем воронку
        stages = []
        values = []
        
        if 'impressions' in df.columns:
            stages.append('Impressions')
            values.append(df['impressions'].sum())
        
        if 'clicks' in df.columns:
            stages.append('Clicks')
            values.append(df['clicks'].sum())
        
        if 'post_click_conversions' in df.columns:
            stages.append('Conversions')
            values.append(df['post_click_conversions'].sum())
        
        if 'revenue' in df.columns:
            stages.append('Revenue')
            values.append(df['revenue'].sum())
        
        if len(stages) < 2:
            return go.Figure()
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker=dict(color=self.colors[:len(stages)])
        ))
        
        fig.update_layout(
            title="Воронка конверсий",
            height=400
        )
        
        return fig

"""
Processing Layer - обработка и агрегация данных
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import config


class DataProcessor:
    """Обработка и расчет метрик"""
    
    @staticmethod
    def calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Расчет производных метрик"""
        df = df.copy()
        
        # CTR
        if 'clicks' in df.columns and 'impressions' in df.columns:
            df['ctr'] = np.where(
                df['impressions'] > 0,
                df['clicks'] / df['impressions'],
                0
            )
        
        # CPM
        if 'TotalSum' in df.columns and 'impressions' in df.columns:
            df['cpm'] = np.where(
                df['impressions'] > 0,
                (df['TotalSum'] / df['impressions']) * 1000,
                0
            )
        
        # CPC
        if 'TotalSum' in df.columns and 'clicks' in df.columns:
            df['cpc'] = np.where(
                df['clicks'] > 0,
                df['TotalSum'] / df['clicks'],
                0
            )
        
        # Conversion Rate (если есть конверсии)
        if 'post_click_conversions' in df.columns and 'clicks' in df.columns:
            df['conversion_rate'] = np.where(
                df['clicks'] > 0,
                df['post_click_conversions'] / df['clicks'],
                0
            )
        
        # CPA (если есть конверсии)
        if 'post_click_conversions' in df.columns and 'TotalSum' in df.columns:
            total_conversions = df.get('post_click_conversions', 0) + df.get('post_view_conversions', 0)
            df['cpa'] = np.where(
                total_conversions > 0,
                df['TotalSum'] / total_conversions,
                0
            )
        
        return df
    
    @staticmethod
    def filter_significant(df: pd.DataFrame, min_impressions: int = None) -> pd.DataFrame:
        """Фильтрация статистически значимых данных"""
        min_impressions = min_impressions or config.MIN_IMPRESSIONS
        
        if 'impressions' in df.columns:
            return df[df['impressions'] >= min_impressions].copy()
        return df
    
    @staticmethod
    def aggregate_by(
        df: pd.DataFrame,
        group_by: List[str],
        metrics: List[str] = None
    ) -> pd.DataFrame:
        """Агрегация данных"""
        if df.empty:
            return df
        
        # Создаем копию для избежания изменения оригинала
        df = df.copy()
        
        # Метрики для суммирования
        sum_metrics = [
            'impressions', 'clicks', 'TotalSum',
            'post_click_conversions', 'post_view_conversions',
            'conversion_value', 'revenue'
        ]
        
        # Метрики для взвешенного среднего
        weighted_metrics = ['viewability', 'vtr', 'frequency']
        
        agg_dict = {}
        
        # Суммы
        for metric in sum_metrics:
            if metric in df.columns:
                agg_dict[metric] = 'sum'
        
        # Взвешенные средние
        for metric in weighted_metrics:
            if metric in df.columns and 'impressions' in df.columns:
                df[f'{metric}_weighted'] = df[metric] * df['impressions']
                agg_dict[f'{metric}_weighted'] = 'sum'
        
        # Агрегация без группировки (общие итоги)
        if not group_by:
            result = pd.DataFrame([df[list(agg_dict.keys())].agg(agg_dict)])
        else:
            # Группировка
            result = df.groupby(group_by, as_index=False, observed=True).agg(agg_dict)
        
        # Пересчет взвешенных средних
        for metric in weighted_metrics:
            if f'{metric}_weighted' in result.columns and 'impressions' in result.columns:
                result[metric] = np.where(
                    result['impressions'] > 0,
                    result[f'{metric}_weighted'] / result['impressions'],
                    0
                )
                result = result.drop(columns=[f'{metric}_weighted'])
        
        # Пересчет производных метрик
        result = DataProcessor.calculate_derived_metrics(result)
        
        return result


class AnalysisEngine:
    """Движок анализа"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.processor = DataProcessor()
    
    def _resolve_advertiser_col(self) -> Optional[str]:
        """Определяет колонку с названием рекламодателя"""
        for col in ('advertiser', 'advertiser_id', 'advertiser_source'):
            if col in self.df.columns:
                return col
        return None

    def compare_advertisers(self) -> pd.DataFrame:
        """Сравнение advertisers"""
        adv_col = self._resolve_advertiser_col()
        if adv_col is None:
            return pd.DataFrame()
        return self.processor.aggregate_by(
            self.df,
            group_by=[adv_col]
        )
    
    def compare_products(self, advertiser: str = None) -> pd.DataFrame:
        """Сравнение продуктов"""
        df = self.df.copy()

        adv_col = self._resolve_advertiser_col()

        if advertiser and adv_col:
            df = df[df[adv_col] == advertiser]

        if 'product' in df.columns:
            group_by = [adv_col, 'product'] if adv_col else ['product']
        else:
            group_by = [adv_col] if adv_col else []

        if not group_by:
            return pd.DataFrame()

        return self.processor.aggregate_by(df, group_by=group_by)
    
    def media_split(self, dimension: str = 'banner_type', per_advertiser: bool = False) -> pd.DataFrame:
        """Медиасплит по измерению, опционально в разрезе advertiser"""
        if dimension not in self.df.columns:
            return pd.DataFrame()

        adv_col = self._resolve_advertiser_col() if per_advertiser else None
        group_by = [adv_col, dimension] if adv_col else [dimension]
        
        result = self.processor.aggregate_by(self.df, group_by=group_by)
        
        # Доля бюджета
        if 'TotalSum' in result.columns:
            total = result['TotalSum'].sum()
            result['spend_share'] = result['TotalSum'] / total if total > 0 else 0
        
        return result
    
    def dynamics(self, period: str = 'M', per_advertiser: bool = False) -> pd.DataFrame:
        """Динамика по периодам (D=день, W=неделя, M=месяц, Q=квартал)"""
        if 'date' not in self.df.columns:
            return pd.DataFrame()
        
        df = self.df.copy()
        df['period'] = df['date'].dt.to_period(period)

        adv_col = self._resolve_advertiser_col() if per_advertiser else None
        group_by = [adv_col, 'period'] if adv_col else ['period']
        
        result = self.processor.aggregate_by(df, group_by=group_by)
        result['period'] = result['period'].astype(str)
        
        return result

    def banner_size_analysis(self, df_banner_size: pd.DataFrame = None) -> pd.DataFrame:
        """
        Анализ BannerSize — только для display.
        df_banner_size: DataFrame со split=BannerSize (должен содержать banner_size).
        """
        df = df_banner_size if df_banner_size is not None else self.df

        if df.empty or 'banner_size' not in df.columns:
            return pd.DataFrame()

        adv_col = None
        for col in ('advertiser', 'advertiser_id', 'advertiser_source'):
            if col in df.columns:
                adv_col = col
                break

        group_by = [adv_col, 'banner_size'] if adv_col else ['banner_size']

        result = self.processor.aggregate_by(df, group_by=group_by)

        if 'TotalSum' in result.columns:
            total = result['TotalSum'].sum()
            result['spend_share'] = result['TotalSum'] / total if total > 0 else 0

        return result
    
    def dmp_analysis(self) -> Dict:
        """Анализ DMP эффективности"""
        return {}
    
    def frequency_analysis(self, bins: List[float] = None) -> pd.DataFrame:
        """Анализ влияния frequency"""
        if 'frequency' not in self.df.columns:
            return pd.DataFrame()
        
        bins = bins or [0, 1, 2, 3, 5, 10, float('inf')]
        labels = [f'{bins[i]}-{bins[i+1]}' for i in range(len(bins)-1)]
        
        df = self.df.copy()
        df['frequency_bucket'] = pd.cut(df['frequency'], bins=bins, labels=labels, include_lowest=True)
        
        return self.processor.aggregate_by(
            df,
            group_by=['frequency_bucket']
        )
    
    def top_performers(self, metric: str = 'ctr', n: int = 10, dimension: str = 'campaign') -> pd.DataFrame:
        """Топ по метрике"""
        if dimension not in self.df.columns or metric not in self.df.columns:
            return pd.DataFrame()
        
        result = self.processor.aggregate_by(
            self.df,
            group_by=[dimension]
        )
        
        # Фильтрация значимых
        result = self.processor.filter_significant(result)
        
        return result.nlargest(n, metric)
    
    def anomalies(self, metric: str = 'ctr', std_threshold: float = 2) -> pd.DataFrame:
        """Поиск аномалий"""
        if metric not in self.df.columns:
            return pd.DataFrame()
        
        df = self.df.copy()
        mean = df[metric].mean()
        std = df[metric].std()
        
        df['z_score'] = (df[metric] - mean) / std if std > 0 else 0
        
        return df[abs(df['z_score']) > std_threshold]
    
    def cohort_analysis(self, period: str = 'M') -> pd.DataFrame:
        """Когортный анализ по периодам"""
        if 'date' not in self.df.columns:
            return pd.DataFrame()
        
        df = self.df.copy()
        df['cohort'] = df['date'].dt.to_period(period)
        
        # Агрегация по когортам и advertiser
        adv_col = self._resolve_advertiser_col()
        if adv_col:
            result = self.processor.aggregate_by(df, group_by=['cohort', adv_col])
        else:
            result = self.processor.aggregate_by(df, group_by=['cohort'])
        
        result['cohort'] = result['cohort'].astype(str)
        return result
    
    def time_of_day_analysis(self) -> pd.DataFrame:
        """Анализ эффективности по времени суток (если есть hour)"""
        if 'date' not in self.df.columns:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        # Если есть hour column - используем её
        if 'hour' not in df.columns:
            # Если date содержит время, извлекаем час
            try:
                df['hour'] = pd.to_datetime(df['date']).dt.hour
            except:
                return pd.DataFrame()
        
        # Группируем по часам
        result = self.processor.aggregate_by(df, group_by=['hour'])
        
        # Добавляем период дня
        def get_period(hour):
            if 0 <= hour < 6:
                return 'Night'
            elif 6 <= hour < 12:
                return 'Morning'
            elif 12 <= hour < 18:
                return 'Afternoon'
            else:
                return 'Evening'
        
        result['period'] = result['hour'].apply(get_period)
        return result.sort_values('hour')
    
    def correlation_analysis(self, metrics: List[str] = None) -> pd.DataFrame:
        """Корреляционный анализ метрик"""
        metrics = metrics or ['ctr', 'viewability', 'frequency', 'cpm']
        
        # Фильтруем только существующие метрики
        available_metrics = [m for m in metrics if m in self.df.columns]
        
        if len(available_metrics) < 2:
            return pd.DataFrame()
        
        # Вычисляем корреляцию
        correlation_matrix = self.df[available_metrics].corr()
        
        return correlation_matrix
    
    def budget_optimization(self) -> Dict:
        """Анализ оптимизации бюджета"""
        adv_col = self._resolve_advertiser_col()
        if adv_col is None or 'TotalSum' not in self.df.columns:
            return {}
        
        advertisers = self.processor.aggregate_by(self.df, group_by=[adv_col])
        
        if advertisers.empty or 'ctr' not in advertisers.columns:
            return {}
        
        # Средний CTR
        avg_ctr = advertisers['ctr'].mean()
        
        # Рекомендации по перераспределению
        underperformers = advertisers[advertisers['ctr'] < avg_ctr * 0.8]
        overperformers = advertisers[advertisers['ctr'] > avg_ctr * 1.2]
        
        total_spend = advertisers['TotalSum'].sum()

        # Унифицируем имя колонки для вывода
        out_cols = [adv_col, 'TotalSum', 'ctr']
        
        result = {
            'total_spend': total_spend,
            'avg_ctr': avg_ctr,
            'underperformers': underperformers[out_cols].rename(columns={adv_col: 'advertiser'}).to_dict('records') if not underperformers.empty else [],
            'overperformers': overperformers[out_cols].rename(columns={adv_col: 'advertiser'}).to_dict('records') if not overperformers.empty else [],
            'potential_savings': underperformers['TotalSum'].sum() if not underperformers.empty else 0
        }
        return result

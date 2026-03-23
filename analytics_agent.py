"""
AI Agent - активный аналитик
Автоматически предлагает дополнительные срезы и анализы
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from ai_layer import InsightGenerator
from processing_layer import AnalysisEngine
import logging

logger = logging.getLogger(__name__)


class AnalyticsAgent:
    """
    AI-агент для активного анализа
    
    Не просто отвечает - ведет анализ:
    - Определяет что анализировать дальше
    - Предлагает дополнительные срезы
    - Находит аномалии и паттерны
    - Рекомендует действия
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Инициализация агента
        
        Args:
            df: DataFrame с данными
        """
        self.df = df
        self.engine = AnalysisEngine(df)
        self.insight_gen = InsightGenerator(df)
        self.analysis_history = []
        self.suggestions = []
    
    def auto_analyze(self) -> Dict:
        """
        Автоматический анализ с предложениями
        
        Returns:
            Полный анализ с рекомендациями дальнейших действий
        """
        results = {
            'initial_analysis': {},
            'deep_dive_suggestions': [],
            'priority_actions': [],
            'additional_questions': []
        }
        
        # 1. Базовый анализ
        logger.info("Этап 1: Базовый анализ...")
        results['initial_analysis'] = self.insight_gen.generate_full_analysis()
        
        # 2. Определяем что нужно анализировать дальше
        logger.info("Этап 2: Определение приоритетов...")
        results['deep_dive_suggestions'] = self._suggest_deep_dives()
        
        # 3. Находим аномалии
        logger.info("Этап 3: Поиск аномалий...")
        anomalies = self._detect_anomalies()
        if anomalies:
            results['anomalies'] = anomalies
            results['priority_actions'].extend([
                f"Изучить аномалию: {a}" for a in anomalies[:3]
            ])
        
        # 4. Предлагаем дополнительные вопросы
        logger.info("Этап 4: Генерация вопросов...")
        results['additional_questions'] = self._generate_questions()
        
        # 5. Находим возможности оптимизации
        logger.info("Этап 5: Поиск возможностей...")
        opportunities = self._find_opportunities()
        results['opportunities'] = opportunities
        
        return results
    
    def _suggest_deep_dives(self) -> List[Dict]:
        """
        Предлагает дополнительные срезы для анализа
        
        Returns:
            Список предложений с приоритетами
        """
        suggestions = []
        
        # Проверяем доступные dimensions
        available_dims = [col for col in self.df.columns 
                         if col in ['campaign', 'product', 'format', 'device', 
                                   'creative', 'placement', 'advertiser_source']]
        
        # 1. Если есть несколько advertisers
        if 'advertiser_source' in self.df.columns and self.df['advertiser_source'].nunique() > 1:
            suggestions.append({
                'priority': 'HIGH',
                'type': 'comparison',
                'suggestion': 'Сравнение эффективности между advertisers',
                'action': 'compare_advertisers',
                'reason': 'Найдено несколько источников данных'
            })
        
        # 2. Проверяем вариативность метрик
        if 'ctr' in self.df.columns:
            ctr_std = self.df['ctr'].std()
            ctr_mean = self.df['ctr'].mean()
            
            if ctr_std / ctr_mean > 0.5:  # Высокая вариативность
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'investigation',
                    'suggestion': 'Высокая вариативность CTR - изучить причины',
                    'action': 'analyze_ctr_variance',
                    'reason': f'Стандартное отклонение CTR: {ctr_std:.4f}'
                })
        
        # 3. Если есть формат и CTR сильно различается
        if 'format' in self.df.columns and 'ctr' in self.df.columns:
            format_ctr = self.df.groupby('format')['ctr'].mean()
            if format_ctr.max() / format_ctr.min() > 2:
                suggestions.append({
                    'priority': 'MEDIUM',
                    'type': 'optimization',
                    'suggestion': 'Перераспределить бюджет в пользу эффективных форматов',
                    'action': 'optimize_format_mix',
                    'reason': f'Разница CTR между форматами: {format_ctr.max()/format_ctr.min():.1f}x'
                })
        
        # 4. Если есть продукты
        if 'product' in self.df.columns:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'deep_dive',
                'suggestion': 'Анализ эффективности по продуктам',
                'action': 'analyze_products',
                'reason': f'Найдено {self.df["product"].nunique()} продуктов'
            })
        
        # 5. Временной анализ
        if 'date' in self.df.columns:
            date_range_days = (self.df['date'].max() - self.df['date'].min()).days
            if date_range_days > 30:
                suggestions.append({
                    'priority': 'MEDIUM',
                    'type': 'trend_analysis',
                    'suggestion': 'Анализ трендов и сезонности',
                    'action': 'analyze_trends',
                    'reason': f'Период: {date_range_days} дней'
                })
        
        return sorted(suggestions, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['priority']])
    
    def _detect_anomalies(self) -> List[str]:
        """
        Поиск аномалий в данных
        
        Returns:
            Список найденных аномалий
        """
        anomalies = []
        
        # 1. Аномальные CTR
        if 'ctr' in self.df.columns:
            ctr_anomalies = self.engine.anomalies(metric='ctr', std_threshold=3)
            if not ctr_anomalies.empty:
                anomalies.append(f"Найдено {len(ctr_anomalies)} аномальных CTR значений")
        
        # 2. Дни без показов
        if 'date' in self.df.columns and 'impressions' in self.df.columns:
            daily = self.df.groupby('date')['impressions'].sum()
            zero_days = daily[daily == 0]
            if len(zero_days) > 0:
                anomalies.append(f"{len(zero_days)} дней без показов")
        
        # 3. Резкие скачки бюджета
        if 'date' in self.df.columns and 'TotalSum' in self.df.columns:
            daily_spend = self.df.groupby('date')['TotalSum'].sum()
            spend_change = daily_spend.pct_change().abs()
            spikes = spend_change[spend_change > 2]  # Изменение более чем в 2 раза
            if len(spikes) > 0:
                anomalies.append(f"{len(spikes)} резких скачков бюджета")
        
        # 4. Нулевые клики при больших показах
        if 'clicks' in self.df.columns and 'impressions' in self.df.columns:
            zero_clicks = self.df[(self.df['impressions'] > 10000) & (self.df['clicks'] == 0)]
            if len(zero_clicks) > 0:
                anomalies.append(f"{len(zero_clicks)} записей с большими показами но нулевыми кликами")
        
        return anomalies
    
    def _generate_questions(self) -> List[str]:
        """
        Генерация дополнительных вопросов для анализа
        
        Returns:
            Список вопросов
        """
        questions = []
        
        # Проверяем что есть в данных
        has_advertiser_source = 'advertiser_source' in self.df.columns and self.df['advertiser_source'].nunique() > 1
        has_products = 'product' in self.df.columns and self.df['product'].nunique() > 1
        has_formats = 'format' in self.df.columns and self.df['format'].nunique() > 1
        
        # Вопросы на основе данных
        if has_advertiser_source:
            questions.append("Какие стратегии лучших advertisers можно масштабировать на других?")
            questions.append("Почему один advertiser эффективнее другого?")
        
        if has_products:
            questions.append("Какие продукты показывают лучший ROI?")
            questions.append("Есть ли продукты, требующие пересмотра стратегии?")
        
        if has_formats:
            questions.append("Какой формат наиболее эффективен для каждого продукта?")
        
        # Универсальные вопросы
        questions.extend([
            "Какие кампании можно остановить или оптимизировать?",
            "Где увеличить бюджет для максимизации эффекта?",
            "Какие гипотезы стоит протестировать?",
            "Есть ли сезонные паттерны в данных?"
        ])
        
        return questions[:10]  # Топ-10 вопросов
    
    def _find_opportunities(self) -> List[Dict]:
        """
        Поиск возможностей для оптимизации
        
        Returns:
            Список возможностей с оценкой impact
        """
        opportunities = []
        
        # 1. Бюджетная оптимизация
        budget_opt = self.engine.budget_optimization()
        if budget_opt and budget_opt.get('potential_savings', 0) > 0:
            opportunities.append({
                'type': 'budget_reallocation',
                'impact': 'HIGH',
                'description': f"Перераспределение бюджета может сэкономить {budget_opt['potential_savings']:,.0f}",
                'action': 'Остановить underperformers и увеличить бюджет на overperformers',
                'potential_value': budget_opt['potential_savings']
            })
        
        # 2. Формат-микс оптимизация
        if 'format' in self.df.columns and 'ctr' in self.df.columns and 'TotalSum' in self.df.columns:
            format_analysis = self.engine.media_split('format')
            if not format_analysis.empty and len(format_analysis) > 1:
                best_format = format_analysis.nlargest(1, 'ctr').iloc[0]
                worst_format = format_analysis.nsmallest(1, 'ctr').iloc[0]
                
                if best_format['ctr'] > worst_format['ctr'] * 1.5:
                    potential_gain = worst_format['TotalSum'] * 0.3  # 30% от плохого формата
                    opportunities.append({
                        'type': 'format_optimization',
                        'impact': 'MEDIUM',
                        'description': f"Переключение с {worst_format.name} на {best_format.name}",
                        'action': f"Увеличить долю {best_format.name} за счет {worst_format.name}",
                        'potential_value': potential_gain
                    })
        
        # 3. Frequency cap оптимизация
        if 'frequency' in self.df.columns and 'ctr' in self.df.columns:
            freq_analysis = self.engine.frequency_analysis()
            if not freq_analysis.empty:
                # Проверяем есть ли перегрев
                high_freq = freq_analysis[freq_analysis.index >= len(freq_analysis) - 2]
                low_freq = freq_analysis[freq_analysis.index < 2]
                
                if not high_freq.empty and not low_freq.empty:
                    if high_freq['ctr'].mean() < low_freq['ctr'].mean() * 0.7:
                        opportunities.append({
                            'type': 'frequency_cap',
                            'impact': 'MEDIUM',
                            'description': 'Снижение frequency cap может улучшить CTR',
                            'action': 'Установить frequency cap ниже текущего',
                            'potential_value': 'Улучшение CTR на 10-20%'
                        })
        
        # 4. Креативы требующие обновления
        if 'creative' in self.df.columns and 'ctr' in self.df.columns:
            creative_performance = self.df.groupby('creative').agg({
                'ctr': 'mean',
                'impressions': 'sum',
                'TotalSum': 'sum'
            })
            
            # Креативы с низким CTR но большим бюджетом
            avg_ctr = creative_performance['ctr'].mean()
            bad_creatives = creative_performance[
                (creative_performance['ctr'] < avg_ctr * 0.8) &
                (creative_performance['TotalSum'] > creative_performance['TotalSum'].quantile(0.75))
            ]
            
            if not bad_creatives.empty:
                opportunities.append({
                    'type': 'creative_refresh',
                    'impact': 'HIGH',
                    'description': f'{len(bad_creatives)} креативов требуют обновления',
                    'action': 'Заменить неэффективные креативы',
                    'potential_value': bad_creatives['TotalSum'].sum()
                })
        
        return sorted(opportunities, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['impact']])
    
    def answer_custom_query(self, query: str) -> Dict:
        """
        Ответ на кастомный запрос пользователя
        
        Args:
            query: естественный запрос (например: "сравни только video")
        
        Returns:
            Результат анализа
        """
        query_lower = query.lower()
        
        # Парсим намерение
        intent = self._parse_intent(query_lower)
        
        # Выполняем соответствующий анализ
        if intent['type'] == 'comparison':
            return self._handle_comparison(intent)
        elif intent['type'] == 'filter':
            return self._handle_filter(intent)
        elif intent['type'] == 'ranking':
            return self._handle_ranking(intent)
        else:
            return {'error': 'Не могу интерпретировать запрос', 'query': query}
    
    def _parse_intent(self, query: str) -> Dict:
        """Парсинг намерения из запроса"""
        intent = {'type': 'unknown', 'filters': {}, 'dimensions': [], 'metric': 'ctr'}
        
        # Ключевые слова для типа запроса
        if any(word in query for word in ['сравни', 'сравнить', 'compare']):
            intent['type'] = 'comparison'
        elif any(word in query for word in ['покажи', 'показать', 'show', 'найди', 'найти']):
            intent['type'] = 'filter'
        elif any(word in query for word in ['топ', 'лучшие', 'top', 'best']):
            intent['type'] = 'ranking'
        
        # Извлекаем фильтры
        if 'video' in query:
            intent['filters']['format'] = 'video'
        if 'banner' in query:
            intent['filters']['format'] = 'banner'
        if 'высок' in query and 'ctr' in query:
            intent['filters']['high_ctr'] = True
        
        # Извлекаем измерения
        if 'продукт' in query or 'product' in query:
            intent['dimensions'].append('product')
        if 'формат' in query or 'format' in query:
            intent['dimensions'].append('format')
        if 'кампани' in query or 'campaign' in query:
            intent['dimensions'].append('campaign')
        
        return intent
    
    def _handle_comparison(self, intent: Dict) -> Dict:
        """Обработка запроса на сравнение"""
        # Применяем фильтры
        df_filtered = self.df.copy()
        
        for key, value in intent['filters'].items():
            if key in df_filtered.columns:
                df_filtered = df_filtered[df_filtered[key] == value]
        
        # Сравниваем по dimensions
        if intent['dimensions']:
            results = {}
            for dim in intent['dimensions']:
                if dim in df_filtered.columns:
                    comparison = self.engine.media_split(dim) if dim in df_filtered.columns else pd.DataFrame()
                    results[dim] = comparison
            return {'type': 'comparison', 'results': results}
        
        return {'type': 'comparison', 'data': df_filtered}
    
    def _handle_filter(self, intent: Dict) -> Dict:
        """Обработка запроса на фильтрацию"""
        df_filtered = self.df.copy()
        
        # Применяем фильтры
        for key, value in intent['filters'].items():
            if key == 'high_ctr' and 'ctr' in df_filtered.columns:
                threshold = df_filtered['ctr'].quantile(0.75)
                df_filtered = df_filtered[df_filtered['ctr'] > threshold]
            elif key in df_filtered.columns:
                df_filtered = df_filtered[df_filtered[key] == value]
        
        return {'type': 'filter', 'data': df_filtered, 'count': len(df_filtered)}
    
    def _handle_ranking(self, intent: Dict) -> Dict:
        """Обработка запроса на ранжирование"""
        metric = intent.get('metric', 'ctr')
        dimension = intent['dimensions'][0] if intent['dimensions'] else 'campaign'
        
        top = self.engine.top_performers(metric=metric, dimension=dimension, n=10)
        
        return {'type': 'ranking', 'metric': metric, 'dimension': dimension, 'top': top}


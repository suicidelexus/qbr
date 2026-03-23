"""
Unit тесты для DSP Analytics Platform
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from processing_layer import DataProcessor, AnalysisEngine
from ai_layer import InsightGenerator


class TestDataProcessor(unittest.TestCase):
    """Тесты для DataProcessor"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.df = pd.DataFrame({
            'impressions': [10000, 20000, 15000],
            'clicks': [100, 150, 120],
            'TotalSum': [120, 240, 180],
            'viewability': [0.8, 0.7, 0.9],
            'frequency': [2.5, 3.0, 2.0],
            'vtr': [0.3, 0.25, 0.35]
        })
    
    def test_calculate_ctr(self):
        """Тест расчета CTR"""
        processor = DataProcessor()
        result = processor.calculate_derived_metrics(self.df)
        
        self.assertIn('ctr', result.columns)
        expected_ctr = 100 / 10000
        self.assertAlmostEqual(result['ctr'].iloc[0], expected_ctr, places=5)
    
    def test_calculate_cpm(self):
        """Тест расчета CPM"""
        processor = DataProcessor()
        result = processor.calculate_derived_metrics(self.df)
        
        self.assertIn('cpm', result.columns)
        expected_cpm = (100 / 10000) * 1000
        self.assertAlmostEqual(result['cpm'].iloc[0], expected_cpm, places=2)
    
    def test_calculate_cpc(self):
        """Тест расчета CPC"""
        processor = DataProcessor()
        result = processor.calculate_derived_metrics(self.df)
        
        self.assertIn('cpc', result.columns)
        expected_cpc = 100 / 100
        self.assertAlmostEqual(result['cpc'].iloc[0], expected_cpc, places=2)
    
    def test_filter_significant(self):
        """Тест фильтрации значимых данных"""
        processor = DataProcessor()
        result = processor.filter_significant(self.df, min_impressions=15000)
        
        self.assertEqual(len(result), 2)  # Должно остаться 2 строки
    
    def test_aggregate_empty_groupby(self):
        """Тест агрегации без группировки"""
        processor = DataProcessor()
        result = processor.aggregate_by(self.df, group_by=[])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result['impressions'].iloc[0], 45000)
        self.assertEqual(result['clicks'].iloc[0], 370)


class TestAnalysisEngine(unittest.TestCase):
    """Тесты для AnalysisEngine"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        self.df = pd.DataFrame({
            'date': dates,
            'advertiser': ['A'] * 5 + ['B'] * 5,
            'product': ['P1'] * 3 + ['P2'] * 7,
            'format': ['video'] * 4 + ['banner'] * 6,
            'impressions': [10000] * 10,
            'clicks': [100] * 10,
            'TotalSum': [120] * 10,
            'viewability': [0.8] * 10,
            'frequency': [2.5] * 10,
            'vtr': [0.3] * 10
        })
        
        processor = DataProcessor()
        self.df = processor.calculate_derived_metrics(self.df)
    
    def test_compare_advertisers(self):
        """Тест сравнения advertisers"""
        engine = AnalysisEngine(self.df)
        result = engine.compare_advertisers()
        
        self.assertFalse(result.empty)
        self.assertEqual(len(result), 2)  # A и B
        self.assertIn('advertiser', result.columns)
    
    def test_media_split(self):
        """Тест медиасплита"""
        engine = AnalysisEngine(self.df)
        result = engine.media_split('format')
        
        self.assertFalse(result.empty)
        self.assertIn('spend_share', result.columns)
        self.assertAlmostEqual(result['spend_share'].sum(), 1.0, places=5)
    
    def test_dynamics(self):
        """Тест динамики"""
        engine = AnalysisEngine(self.df)
        result = engine.dynamics('D')
        
        self.assertFalse(result.empty)
        self.assertIn('period', result.columns)
    
    def test_dmp_analysis(self):
        """Тест DMP анализа"""
        engine = AnalysisEngine(self.df)
        result = engine.dmp_analysis()
        
        self.assertIsInstance(result, dict)
        self.assertIn('dmp_share', result)
    
    def test_frequency_analysis(self):
        """Тест frequency анализа"""
        engine = AnalysisEngine(self.df)
        result = engine.frequency_analysis()
        
        self.assertFalse(result.empty)
        self.assertIn('frequency_bucket', result.columns)
    
    def test_correlation_analysis(self):
        """Тест корреляционного анализа"""
        engine = AnalysisEngine(self.df)
        result = engine.correlation_analysis()
        
        self.assertFalse(result.empty)
        self.assertEqual(result.shape[0], result.shape[1])  # Квадратная матрица
    
    def test_budget_optimization(self):
        """Тест оптимизации бюджета"""
        # Создаем данные с разными CTR
        df = self.df.copy()
        df.loc[df['advertiser'] == 'A', 'clicks'] = 50  # Низкий CTR
        df.loc[df['advertiser'] == 'B', 'clicks'] = 150  # Высокий CTR
        
        processor = DataProcessor()
        df = processor.calculate_derived_metrics(df)
        
        engine = AnalysisEngine(df)
        result = engine.budget_optimization()
        
        self.assertIsInstance(result, dict)
        self.assertIn('avg_ctr', result)
        self.assertIn('underperformers', result)
        self.assertIn('overperformers', result)


class TestInsightGenerator(unittest.TestCase):
    """Тесты для InsightGenerator"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
        np.random.seed(42)
        
        self.df = pd.DataFrame({
            'date': dates,
            'advertiser': np.random.choice(['A', 'B', 'C'], len(dates)),
            'product': np.random.choice(['P1', 'P2'], len(dates)),
            'format': np.random.choice(['video', 'banner'], len(dates)),
            'impressions': np.random.randint(10000, 50000, len(dates)),
            'clicks': np.random.randint(100, 500, len(dates)),
            'TotalSum': np.random.uniform(120, 600, len(dates)),
            'viewability': np.random.uniform(0.6, 0.9, len(dates)),
            'frequency': np.random.uniform(1, 5, len(dates)),
            'vtr': np.random.uniform(0.2, 0.4, len(dates))
        })
        
        processor = DataProcessor()
        self.df = processor.calculate_derived_metrics(self.df)
    
    def test_generate_full_analysis(self):
        """Тест полного анализа"""
        gen = InsightGenerator(self.df)
        results = gen.generate_full_analysis()
        
        self.assertIsInstance(results, dict)
        self.assertIn('tldr', results)
        self.assertIn('advertisers', results)
        self.assertIn('dynamics', results)
        self.assertIn('recommendations', results)
    
    def test_tldr_generation(self):
        """Тест генерации TL;DR"""
        gen = InsightGenerator(self.df)
        tldr = gen._generate_tldr()
        
        self.assertIsInstance(tldr, str)
        self.assertIn('бюджет', tldr.lower())
        self.assertIn('ctr', tldr.lower())
    
    def test_recommendations_created(self):
        """Тест создания рекомендаций"""
        gen = InsightGenerator(self.df)
        results = gen.generate_full_analysis()
        
        # Должны быть хоть какие-то рекомендации или инсайты
        total_items = (
            len(results['recommendations']) +
            len(results['hypotheses']) +
            len(results['advertisers']['insights'])
        )
        self.assertGreater(total_items, 0)


def run_tests():
    """Запуск всех тестов"""
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestDataProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestInsightGenerator))
    
    # Запускаем
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_tests()
    
    # Выводим summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)
    
    # Exit code для CI/CD
    exit(0 if result.wasSuccessful() else 1)


"""
DSP Analytics Platform - Main Entry Point
AI-ядро аналитической платформы для DSP
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from data_layer import DataLoader, DSPClient
from processing_layer import DataProcessor
from ai_layer import InsightGenerator
from visualization import ChartGenerator
from report_generator import ReportGenerator


def analyze_dsp_data(
    source: str = 'api',
    filepath: str = None,
    start_date: str = None,
    end_date: str = None,
    output_dir: str = './output'
):
    """
    Главная функция анализа DSP данных
    
    Args:
        source: 'api', 'csv', или 'excel'
        filepath: путь к файлу (для csv/excel)
        start_date: дата начала (для API)
        end_date: дата окончания (для API)
        output_dir: директория для результатов
    """
    print("=" * 60)
    print("DSP ANALYTICS PLATFORM")
    print("=" * 60)
    
    # 1. Загрузка данных
    print("\n[1/5] Загрузка данных...")
    loader = DataLoader()
    
    if source == 'api':
        client = DSPClient()  # credentials из config / .env
        if not start_date or not end_date:
            df = client.get_last_n_days(30)
        else:
            df = client.get_report(start_date=start_date, end_date=end_date)
    elif source == 'csv':
        df = loader.load_from_csv(filepath)
    elif source == 'excel':
        df = loader.load_from_excel(filepath)
    else:
        raise ValueError(f"Неизвестный источник: {source}")
    
    if df.empty:
        print("[X] Нет данных для анализа")
        return
    
    print(f"[OK] Загружено {len(df)} строк")
    
    # 2. Обработка данных
    print("\n[2/5] Обработка данных...")
    processor = DataProcessor()
    df = processor.calculate_derived_metrics(df)
    df = processor.filter_significant(df)
    print(f"[OK] После фильтрации: {len(df)} строк")
    
    # 3. Генерация инсайтов
    print("\n[3/5] Анализ и генерация инсайтов...")
    insight_gen = InsightGenerator(df)
    results = insight_gen.generate_full_analysis()
    print("[OK] Анализ завершен")
    
    # 4. Визуализация
    print("\n[4/5] Генерация графиков...")
    chart_gen = ChartGenerator()
    charts = chart_gen.generate_all_charts(results, output_dir=f'{output_dir}/charts')
    print(f"[OK] Создано {len(charts)} графиков")
    
    # 5. Генерация отчета
    print("\n[5/5] Генерация отчета...")
    report_gen = ReportGenerator(results)
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    report_gen.save_markdown(f'{output_dir}/report.md')
    report_gen.save_json(f'{output_dir}/results.json')
    print(f"[OK] Отчет сохранен в {output_dir}")
    
    # Вывод ключевых инсайтов
    print("\n" + "=" * 60)
    print("КЛЮЧЕВЫЕ ИНСАЙТЫ")
    print("=" * 60)
    print(results['tldr'])
    
    print("\n[ADVERTISERS]:")
    for insight in results['advertisers']['insights'][:3]:
        print(f"  - {insight}")
    
    print("\n[ДИНАМИКА]:")
    for insight in results['dynamics']['insights'][:3]:
        print(f"  - {insight}")
    
    print("\n[РЕКОМЕНДАЦИИ]:")
    for i, rec in enumerate(results['recommendations'][:3], 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 60)
    print(f"Полный отчет: {output_dir}/report.md")
    print("=" * 60)
    
    return results


def demo_with_sample_data():
    """Демо с синтетическими данными"""
    import numpy as np
    from datetime import datetime, timedelta
    
    print("Генерация демо-данных...")
    
    # Создание синтетических данных
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    advertisers = ['Advertiser A', 'Advertiser B', 'Advertiser C']
    products = ['Product 1', 'Product 2', 'Product 3']
    formats = ['video', 'banner', 'native']
    
    data = []
    for date in dates:
        for advertiser in advertisers:
            for product in products:
                for fmt in formats:
                    impressions = np.random.randint(10000, 100000)
                    clicks = int(impressions * np.random.uniform(0.001, 0.005))
                    total_sum = impressions * np.random.uniform(1, 5) / 1000
                    
                    data.append({
                        'date': date,
                        'advertiser': advertiser,
                        'product': product,
                        'format': fmt,
                        'impressions': impressions,
                        'clicks': clicks,
                        'TotalSum': total_sum,
                        'viewability': np.random.uniform(0.6, 0.9),
                        'frequency': np.random.uniform(1, 5),
                        'vtr': np.random.uniform(0.2, 0.4) if fmt == 'video' else 0
                    })
    
    df = pd.DataFrame(data)
    
    # Сохранение демо-данных
    df.to_csv('demo_data.csv', index=False)
    print(f"[OK] Демо-данные созданы: demo_data.csv ({len(df)} строк)")
    
    # Запуск анализа
    return analyze_dsp_data(source='csv', filepath='demo_data.csv')


if __name__ == '__main__':
    # Выбор режима работы
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'demo':
            # Демо режим
            demo_with_sample_data()
        elif sys.argv[1] == 'api':
            # API режим
            analyze_dsp_data(source='api')
        else:
            # CSV/Excel файл
            filepath = sys.argv[1]
            source = 'excel' if filepath.endswith('.xlsx') else 'csv'
            analyze_dsp_data(source=source, filepath=filepath)
    else:
        # По умолчанию - демо
        print("Использование:")
        print("  python main.py demo              - демо с синтетическими данными")
        print("  python main.py api               - загрузка из API")
        print("  python main.py data.csv          - анализ CSV файла")
        print("  python main.py data.xlsx         - анализ Excel файла")
        print("\nЗапуск демо режима...\n")
        demo_with_sample_data()


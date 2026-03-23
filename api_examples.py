"""
Примеры работы с DSP API
"""
from data_layer import DSPClient, DataLoader
from processing_layer import DataProcessor, AnalysisEngine
from ai_layer import InsightGenerator
from visualization import ChartGenerator
import pandas as pd


# ==================== ПРИМЕР 1: Базовая работа с API ====================

def example_basic_api():
    """Базовое использование DSP API"""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Базовая работа с API")
    print("="*60)
    
    # Создание клиента
    client = DSPClient()
    
    # Тест подключения
    if not client.test_connection():
        print("[!] Ошибка подключения к API")
        return
    
    # Получение данных за последние 7 дней
    print("\nЗагрузка данных за последние 7 дней...")
    df = client.get_last_n_days(days=7)
    
    if not df.empty:
        print(f"[OK] Загружено {len(df)} строк")
        print(f"\nКолонки: {list(df.columns)}")
        print(f"\nПервые строки:")
        print(df.head())
    else:
        print("[!] Нет данных")


# ==================== ПРИМЕР 2: Отчет за период ====================

def example_period_report():
    """Получение отчета за конкретный период"""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Отчет за период")
    print("="*60)
    
    client = DSPClient()
    
    # Загрузка данных за январь 2024
    print("\nЗагрузка данных за январь 2024...")
    df = client.get_report(
        start_date='2024-01-01',
        end_date='2024-01-31',
        metrics=['impressions', 'clicks', 'ctr', 'TotalSum', 'cpm'],
        dimensions=['date', 'advertiser', 'campaign'],
        filters={
            'campaign_status': 'active'
        }
    )
    
    if not df.empty:
        print(f"[OK] Загружено {len(df)} строк")
        
        # Базовая статистика
        print(f"\nОбщая статистика:")
        print(f"- Impressions: {df['impressions'].sum():,.0f}")
        print(f"- Clicks: {df['clicks'].sum():,.0f}")
        print(f"- CTR: {df['ctr'].mean():.3%}")
        print(f"- Total Spend: ${df['TotalSum'].sum():,.2f}")


# ==================== ПРИМЕР 3: Работа с кампаниями ====================

def example_campaigns():
    """Получение и анализ кампаний"""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Работа с кампаниями")
    print("="*60)
    
    client = DSPClient()
    
    # Получение всех активных кампаний
    print("\nПолучение активных кампаний...")
    campaigns = client.get_campaigns(status='active')
    
    if not campaigns.empty:
        print(f"[OK] Найдено {len(campaigns)} активных кампаний")
        print(f"\nКампании:")
        for _, camp in campaigns.iterrows():
            print(f"  - {camp.get('name', 'N/A')} (ID: {camp.get('id', 'N/A')})")
        
        # Получение performance для этих кампаний
        print("\nЗагрузка performance кампаний...")
        campaign_ids = campaigns['id'].tolist()
        
        df = client.get_last_n_days(
            days=30,
            dimensions=['campaign'],
            filters={'campaign_id': campaign_ids}
        )
        
        if not df.empty:
            print(f"[OK] Загружено {len(df)} строк")
            
            # Топ кампаний по CTR
            top_campaigns = df.nlargest(5, 'ctr')
            print(f"\nТоп-5 кампаний по CTR:")
            for _, row in top_campaigns.iterrows():
                print(f"  - {row['campaign']}: {row['ctr']:.3%}")


# ==================== ПРИМЕР 4: Анализ креативов ====================

def example_creatives():
    """Анализ эффективности креативов"""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Анализ креативов")
    print("="*60)
    
    client = DSPClient()
    
    # Получение креативов
    print("\nПолучение креативов...")
    creatives = client.get_creatives(
        format='video',
        status='active'
    )
    
    if not creatives.empty:
        print(f"[OK] Найдено {len(creatives)} видео-креативов")
        
        # Получаем performance
        creative_ids = creatives['id'].tolist()
        
        df = client.get_last_n_days(
            days=30,
            dimensions=['creative_id'],
            filters={'creative_id': creative_ids}
        )
        
        if not df.empty and 'vtr' in df.columns:
            # Лучшие креативы по VTR
            best = df.nlargest(10, 'vtr')
            print(f"\nТоп-10 креативов по VTR:")
            for _, row in best.iterrows():
                print(f"  - Creative {row['creative_id']}: {row.get('vtr', 0):.1%}")


# ==================== ПРИМЕР 5: Полный анализ с AI ====================

def example_full_analysis():
    """Полный цикл: API → Анализ → AI-инсайты"""
    print("\n" + "="*60)
    print("ПРИМЕР 5: Полный анализ с AI")
    print("="*60)
    
    # 1. Загрузка данных
    print("\n[1/4] Загрузка данных из API...")
    loader = DataLoader()
    df = loader.dsp_client.get_last_n_days(
        days=30,
        dimensions=['date', 'advertiser', 'campaign', 'format']
    )
    
    if df.empty:
        print("[!] Нет данных")
        return
    
    print(f"[OK] Загружено {len(df)} строк")
    
    # 2. Обработка
    print("\n[2/4] Обработка данных...")
    processor = DataProcessor()
    df = processor.calculate_derived_metrics(df)
    df = processor.filter_significant(df)
    print(f"[OK] После обработки: {len(df)} строк")
    
    # 3. AI-анализ
    print("\n[3/4] Генерация AI-инсайтов...")
    gen = InsightGenerator(df)
    results = gen.generate_full_analysis()
    print("[OK] Анализ завершен")
    
    # 4. Вывод результатов
    print("\n[4/4] Результаты:")
    print("\n" + "="*60)
    print("TL;DR")
    print("="*60)
    print(results['tldr'])
    
    print("\n" + "="*60)
    print("Ключевые инсайты")
    print("="*60)
    for insight in results['advertisers']['insights'][:5]:
        print(f"• {insight}")
    
    print("\n" + "="*60)
    print("Рекомендации")
    print("="*60)
    for i, rec in enumerate(results['recommendations'][:5], 1):
        print(f"{i}. {rec}")


# ==================== ПРИМЕР 6: Мониторинг performance ====================

def example_monitoring():
    """Мониторинг performance кампаний"""
    print("\n" + "="*60)
    print("ПРИМЕР 6: Мониторинг performance")
    print("="*60)
    
    client = DSPClient()
    
    # Получаем данные за вчера
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\nПроверка performance за {yesterday}...")
    df = client.get_report(
        start_date=yesterday,
        end_date=yesterday,
        dimensions=['campaign']
    )
    
    if not df.empty:
        # Находим проблемные кампании
        low_ctr = df[df['ctr'] < 0.001]
        
        if not low_ctr.empty:
            print(f"\n[!] Найдено {len(low_ctr)} кампаний с низким CTR:")
            for _, row in low_ctr.iterrows():
                print(f"  - {row['campaign']}: CTR {row['ctr']:.3%}, {row['impressions']:,.0f} показов")
        else:
            print("[OK] Все кампании в норме")
        
        # Находим высокозатратные
        high_spend = df.nlargest(5, 'TotalSum')
        print(f"\nТоп-5 по бюджету:")
        for _, row in high_spend.iterrows():
            print(f"  - {row['campaign']}: ${row['TotalSum']:,.2f}")


# ==================== ПРИМЕР 7: Сравнение периодов ====================

def example_period_comparison():
    """Сравнение текущего и прошлого месяца"""
    print("\n" + "="*60)
    print("ПРИМЕР 7: Сравнение периодов")
    print("="*60)
    
    client = DSPClient()
    
    # Текущий месяц
    print("\nЗагрузка данных текущего месяца...")
    current = client.get_report(
        start_date='2024-03-01',
        end_date='2024-03-31',
        dimensions=['advertiser']
    )
    
    # Прошлый месяц
    print("Загрузка данных прошлого месяца...")
    previous = client.get_report(
        start_date='2024-02-01',
        end_date='2024-02-29',
        dimensions=['advertiser']
    )
    
    if not current.empty and not previous.empty:
        # Сравнение
        comparison = pd.merge(
            current,
            previous,
            on='advertiser',
            suffixes=('_current', '_previous')
        )
        
        comparison['ctr_change'] = (
            (comparison['ctr_current'] - comparison['ctr_previous']) 
            / comparison['ctr_previous']
        )
        
        print("\nИзменение CTR по рекламодателям:")
        for _, row in comparison.iterrows():
            change = row['ctr_change']
            symbol = "📈" if change > 0 else "📉"
            print(f"  {symbol} {row['advertiser']}: {change:+.1%}")


# ==================== ПРИМЕР 8: Экспорт данных ====================

def example_export():
    """Экспорт данных из API"""
    print("\n" + "="*60)
    print("ПРИМЕР 8: Экспорт данных")
    print("="*60)
    
    client = DSPClient()
    
    # Загрузка
    print("\nЗагрузка данных...")
    df = client.get_last_n_days(days=30)
    
    if not df.empty:
        # Сохранение в разные форматы
        print("\nСохранение в файлы...")
        
        df.to_csv('export/dsp_data.csv', index=False)
        print("[OK] Сохранено в CSV: export/dsp_data.csv")
        
        df.to_excel('export/dsp_data.xlsx', index=False)
        print("[OK] Сохранено в Excel: export/dsp_data.xlsx")
        
        df.to_json('export/dsp_data.json', orient='records')
        print("[OK] Сохранено в JSON: export/dsp_data.json")


# ==================== ПРИМЕР 9: Batch загрузка ====================

def example_batch_loading():
    """Загрузка больших объемов данных по частям"""
    print("\n" + "="*60)
    print("ПРИМЕР 9: Batch загрузка")
    print("="*60)
    
    client = DSPClient()
    
    # Загрузка по месяцам
    print("\nЗагрузка данных за Q1 2024 по месяцам...")
    
    months = [
        ('2024-01-01', '2024-01-31', 'Январь'),
        ('2024-02-01', '2024-02-29', 'Февраль'),
        ('2024-03-01', '2024-03-31', 'Март')
    ]
    
    all_data = []
    
    for start, end, name in months:
        print(f"\nЗагрузка {name}...")
        df = client.get_report(
            start_date=start,
            end_date=end,
            use_pagination=True
        )
        
        if not df.empty:
            print(f"[OK] {name}: {len(df)} строк")
            all_data.append(df)
        else:
            print(f"[!] {name}: нет данных")
    
    # Объединение
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        print(f"\n[OK] Всего загружено: {len(combined)} строк")
        
        # Базовая статистика
        print(f"\nСтатистика за Q1 2024:")
        print(f"- Impressions: {combined['impressions'].sum():,.0f}")
        print(f"- Clicks: {combined['clicks'].sum():,.0f}")
        print(f"- CTR: {combined['ctr'].mean():.3%}")


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def run_all_examples():
    """Запуск всех примеров"""
    examples = [
        ("Базовая работа с API", example_basic_api),
        ("Отчет за период", example_period_report),
        ("Работа с кампаниями", example_campaigns),
        ("Анализ креативов", example_creatives),
        ("Полный анализ с AI", example_full_analysis),
        ("Мониторинг performance", example_monitoring),
        ("Сравнение периодов", example_period_comparison),
        ("Экспорт данных", example_export),
        ("Batch загрузка", example_batch_loading)
    ]
    
    print("\n" + "="*60)
    print("DSP API - ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ")
    print("="*60)
    print("\nДоступные примеры:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    choice = input("\nВыберите пример (1-9) или 'all' для всех: ")
    
    if choice.lower() == 'all':
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\n[!] Ошибка в примере '{name}': {e}")
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                examples[idx][1]()
            else:
                print("Неверный номер примера")
        except ValueError:
            print("Введите число или 'all'")


if __name__ == '__main__':
    # Запуск примеров
    run_all_examples()


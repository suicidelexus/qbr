# DSP Analytics Platform

AI-ядро аналитической платформы для DSP (Demand-Side Platform)

**🚀 Версия 3.1.0 - Multi-Advertiser + ClickHouse Edition**

## Поддерживаемые интеграции

- ✅ **Hybrid.ai API** (REST API 3.0) - https://docs.hybrid.ai/rest-api-3-0
- ✅ **ClickHouse** - автоматический маппинг 80+ колонок
- ✅ **Multi-Advertiser** - параллельная работа с несколькими рекламодателями
- ✅ **CSV/Excel** - загрузка из файлов
- ✅ **Google Export** - Slides и Sheets

## Возможности

- 📊 **Анализ данных DSP** - глубокий анализ показателей рекламных кампаний
- 👥 **Multi-Advertiser режим** - сравнение нескольких рекламодателей одновременно
- 🔍 **Сравнение advertisers** - кто эффективнее и за счет чего
- 🔀 **Кросс-анализ** - advertiser × product/format/campaign
- 📈 **Динамика метрик** - MoM/QoQ/YoY изменения
- 🎯 **DMP анализ** - эффективность сегментов и влияние на KPI
- 🔄 **Frequency анализ** - оптимальная частота показов
- 🤖 **AI-Агент** - активный анализ с предложениями дополнительных срезов
- 💡 **AI-инсайты** - автоматическая генерация выводов
- 💬 **Кастомные запросы** - обработка естественного языка
- 📋 **Отчеты** - Markdown, JSON, Google Slides/Sheets
- 📊 **Визуализация** - интерактивные графики Plotly
- 🔗 **Корреляционный анализ** - взаимосвязь метрик
- 💰 **Оптимизация бюджета** - рекомендации по перераспределению
- 🌐 **Streamlit Dashboard** - два режима: Single и Multi-Advertiser
- ⚙️ **Automation Generator** - генерация кода для cron/Docker/GitHub Actions
- ✅ **Unit тесты** - покрытие основной функциональности

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│                   DATA LAYER                        │
│  - DSP API Client                                   │
│  - CSV/Excel Loader                                 │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              PROCESSING LAYER                       │
│  - Metrics Calculation                              │
│  - Aggregation                                      │
│  - Filtering                                        │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                  AI LAYER                           │
│  - Insight Generation                               │
│  - Recommendations                                  │
│  - Hypotheses                                       │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                OUTPUT LAYER                         │
│  - Visualization (Plotly)                           │
│  - Reports (MD, JSON)                               │
│  - Google Slides                                    │
└─────────────────────────────────────────────────────┘
```

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

### Минимальная настройка (только API Key):

```env
# В .env файле нужно только это:
DSP_API_KEY=your_api_key_here
```

**Или через Dashboard UI:**
1. Запустите `streamlit run dashboard.py`
2. Раскройте "🔑 API Credentials"
3. Вставьте только API Key
4. Нажмите "Тест"

**Полная настройка** (если нужно):

```env
DSP_API_KEY=your_api_key_here
DSP_API_URL=https://api.dsp-platform.com/v1  # опционально
DSP_CLIENT_ID=your_client_id  # редко нужен
```

**Быстрая проверка:**
```bash
python test_api.py
```

**Подробнее:** 
- [API_URL_EXPLAINED.md](API_URL_EXPLAINED.md) - что такое API URL и нужен ли он?
- [DASHBOARD_API_SETUP.md](DASHBOARD_API_SETUP.md) - настройка через интерфейс
- [API_SETUP.md](API_SETUP.md) - настройка через .env

## Использование

### Демо режим

```bash
python main.py demo
```

Создает синтетические данные и выполняет полный анализ.

### Анализ CSV/Excel

```bash
python main.py data.csv
python main.py data.xlsx
```

### Загрузка из API

```bash
python main.py api
```

### Streamlit Dashboard

```bash
streamlit run dashboard.py
```

Запускает интерактивный веб-интерфейс с визуализацией и анализом в реальном времени.

### Запуск тестов

```bash
python tests.py
```

Выполняет 15 unit тестов для проверки корректности работы.

### Программный интерфейс

```python
from data_layer import DataLoader
from ai_layer import InsightGenerator
from visualization import ChartGenerator

# Загрузка данных
loader = DataLoader()
df = loader.load_from_csv('data.csv')

# Анализ
insight_gen = InsightGenerator(df)
results = insight_gen.generate_full_analysis()

# Визуализация
chart_gen = ChartGenerator()
charts = chart_gen.generate_all_charts(results)

# Отчет
from report_generator import ReportGenerator
report = ReportGenerator(results)
report.save_markdown('report.md')
```

## Структура проекта

```
qbr/
├── main.py                 # Точка входа
├── config.py              # Конфигурация
├── data_layer.py          # Работа с данными
├── processing_layer.py    # Обработка и агрегация
├── ai_layer.py            # AI-инсайты
├── visualization.py       # Графики
├── report_generator.py    # Генерация отчетов
├── requirements.txt       # Зависимости
└── .env                   # Настройки (не в git)
```

## Метрики

### Основные
- Impressions
- Clicks
- CTR
- CPC
- CPM
- Viewability
- VTR
- Frequency
- DMP Cost
- Media Spend
- Total Spend

### Конверсионные
- Post-click conversions
- Post-view conversions
- Conversion value
- Revenue

## Типы анализа

1. **Advertiser Comparison** - сравнение рекламодателей
2. **Product Analysis** - анализ продуктов/категорий
3. **Media Split** - распределение по форматам
4. **Performance** - эффективность кампаний
5. **Dynamics** - изменение метрик во времени
6. **DMP Analysis** - эффективность сегментов
7. **Frequency Analysis** - влияние частоты показов
8. **Conversion Analysis** - конверсионная воронка

## Результаты

После запуска создается папка `output/`:

```
output/
├── report.md              # Markdown отчет
├── results.json           # JSON с данными
└── charts/                # HTML графики
    ├── advertisers.html
    ├── media_split.html
    ├── dynamics.html
    └── dmp.html
```

## API запросы

Пример запроса к DSP API:

```python
client = DSPClient()
df = client.get_data(
    start_date='2024-01-01',
    end_date='2024-03-31',
    metrics=['impressions', 'clicks', 'ctr', 'viewability'],
    dimensions=['advertiser', 'product', 'format'],
    filters={'advertiser': 'Advertiser A'}
)
```

## Расширение системы

### Добавление новой метрики

```python
# В config.py
CORE_METRICS.append('new_metric')

# В processing_layer.py
def calculate_derived_metrics(df):
    df['new_metric'] = df['metric_a'] / df['metric_b']
    return df
```

### Добавление нового типа анализа

```python
# В processing_layer.py
class AnalysisEngine:
    def new_analysis(self):
        # Ваш анализ
        return result
```

### Добавление нового графика

```python
# В visualization.py
class ChartGenerator:
    def new_chart(self, df):
        fig = go.Figure(...)
        return fig
```

## Принципы разработки

✅ Чистый код
✅ Минимум файлов
✅ Переиспользование
✅ Масштабируемость
✅ Читаемость

## Лицензия

MIT

## Автор

DSP Analytics Platform - AI-powered solution


# 🚀 Multi-Advertiser Mode - Полное руководство

## Обзор

Multi-Advertiser режим позволяет работать с несколькими рекламодателями одновременно, сравнивать их эффективность и находить лучшие стратегии.

---

## ⚡ Быстрый старт

### Шаг 1: Запустите Multi-Advertiser Dashboard

```bash
streamlit run dashboard_multi.py
```

### Шаг 2: Добавьте Advertisers

В боковой панели:
1. Раскройте **"➕ Добавить Advertiser"**
2. Введите название (например: "Advertiser A")
3. Вставьте API Key
4. Нажмите **"➕ Добавить"**
5. Повторите для других advertisers

### Шаг 3: Загрузите данные

1. Выберите период (30 дней)
2. Нажмите **"📥 Загрузить данные"**
3. Данные загрузятся параллельно от всех advertisers

### Шаг 4: Анализируйте!

Используйте 5 вкладок:
- **Сравнение Advertisers** - кто эффективнее
- **Кросс-анализ** - advertiser × dimension
- **AI-Агент** - автоматические рекомендации
- **Кастомные запросы** - естественный язык
- **Экспорт & Автоматизация** - генерация кода

---

## 📊 Возможности

### 1. Parallel Data Loading

```python
from multi_advertiser import MultiAdvertiserManager

credentials = [
    {"advertiser": "Advertiser A", "api_key": "key1"},
    {"advertiser": "Advertiser B", "api_key": "key2"},
    {"advertiser": "Advertiser C", "api_key": "key3"}
]

manager = MultiAdvertiserManager(credentials=credentials)

# Параллельная загрузка от всех
df = manager.load_data(
    start_date='2024-01-01',
    end_date='2024-03-31',
    parallel=True  # Ускоряет в N раз
)
```

### 2. Data Validation

```python
# Проверка совместимости данных
validation = manager.validate_data_compatibility(df)

print(validation['status'])         # 'ok' или 'issues'
print(validation['advertisers_count'])  # Количество advertisers
print(validation['issues'])         # Список проблем
print(validation['warnings'])       # Предупреждения
```

### 3. Comparison Summary

```python
# Сводка по всем advertisers
summary = manager.get_comparison_summary(df)

# Ранжирование
summary = summary.sort_values('ctr', ascending=False)

# Топ advertiser
best = summary.iloc[0]
print(f"Лучший: {best['advertiser_source']} - CTR {best['ctr']:.3%}")
```

### 4. Cross-Analysis

```python
# Advertiser × Product
comparison = manager.compare_by_dimension(df, dimension='product')

# Advertiser × Format
comparison = manager.compare_by_dimension(df, dimension='format')

# Лучшие комбинации
top = manager.find_best_performers(
    df,
    metric='ctr',
    dimension='product',
    top_n=10
)
```

### 5. AI Agent

```python
from analytics_agent import AnalyticsAgent

agent = AnalyticsAgent(df)

# Автоматический анализ
analysis = agent.auto_analyze()

# Результаты:
# - initial_analysis: базовый анализ
# - deep_dive_suggestions: рекомендации для углубления
# - priority_actions: приоритетные действия
# - additional_questions: вопросы для изучения
# - opportunities: возможности оптимизации
# - anomalies: найденные аномалии
```

### 6. Custom Queries

```python
# Обработка естественных запросов
result = agent.answer_custom_query("сравни только video")

# Поддерживаемые типы:
# - Сравнение: "сравни форматы"
# - Фильтрация: "покажи высокий CTR"
# - Ранжирование: "топ продуктов"
```

### 7. Automation Generator

```python
from automation_generator import AutomationGenerator

gen = AutomationGenerator()

# Генерация скрипта
script = gen.generate_scheduler_script(
    credentials=credentials,
    schedule_type='daily'
)

# Сохранение
with open('automation_script.py', 'w') as f:
    f.write(script)

# Также генерируются:
# - cron_config.txt
# - docker-compose.yml
# - Dockerfile
# - GitHub Actions workflow
```

---

## 🎯 Сценарии использования

### Сценарий 1: Weekly Review

```python
from multi_advertiser import MultiAdvertiserManager
from analytics_agent import AnalyticsAgent

# 1. Загрузка данных за неделю
manager = MultiAdvertiserManager(credentials=credentials)
df = manager.load_data(
    start_date='2024-03-17',
    end_date='2024-03-23',
    parallel=True
)

# 2. Сравнение advertisers
summary = manager.get_comparison_summary(df)
print(summary[['advertiser_source', 'ctr', 'total_spend']])

# 3. AI анализ
agent = AnalyticsAgent(df)
analysis = agent.auto_analyze()

# 4. Приоритетные действия
for action in analysis['priority_actions']:
    print(f"⚠️ {action}")

# 5. Возможности
for opp in analysis['opportunities']:
    print(f"💰 {opp['description']}")
```

### Сценарий 2: Performance Benchmarking

```python
# Кто эффективнее и почему?

# 1. Базовое сравнение
summary = manager.get_comparison_summary(df)
best = summary.nlargest(1, 'ctr').iloc[0]
worst = summary.nsmallest(1, 'ctr').iloc[0]

print(f"Лучший: {best['advertiser_source']} - {best['ctr']:.3%}")
print(f"Худший: {worst['advertiser_source']} - {worst['ctr']:.3%}")

# 2. Детальный анализ по форматам
format_comparison = manager.compare_by_dimension(df, 'format')

# Pivot таблица
pivot = format_comparison.pivot_table(
    index='advertiser_source',
    columns='format',
    values='ctr'
)
print(pivot)

# 3. Лучшие практики
# Найти что делает лидер по CTR
best_practices = df[df['advertiser_source'] == best['advertiser_source']]
best_format = best_practices.groupby('format')['ctr'].mean().idxmax()
best_product = best_practices.groupby('product')['ctr'].mean().idxmax()

print(f"Лидер использует:")
print(f"  - Формат: {best_format}")
print(f"  - Продукт: {best_product}")
```

### Сценарий 3: Budget Optimization

```python
# Найти где перераспределить бюджет

# 1. Efficiency по advertiser
summary = manager.get_comparison_summary(df)

# 2. Underperformers (низкий CTR, высокий spend)
avg_ctr = summary['ctr'].mean()
avg_spend = summary['total_spend'].mean()

underperformers = summary[
    (summary['ctr'] < avg_ctr * 0.8) &
    (summary['total_spend'] > avg_spend)
]

# 3. Overperformers (высокий CTR, любой spend)
overperformers = summary[
    summary['ctr'] > avg_ctr * 1.2
]

# 4. Рекомендации
print("Underperformers (снизить бюджет):")
print(underperformers[['advertiser_source', 'ctr', 'total_spend']])

print("\nOverperformers (увеличить бюджет):")
print(overperformers[['advertiser_source', 'ctr', 'total_spend']])

# Потенциальная экономия
savings = underperformers['total_spend'].sum() * 0.3  # 30% cut
print(f"\nПотенциальная экономия: {savings:,.0f}")
```

### Сценарий 4: Automated Reporting

```python
from automation_generator import generate_full_automation_package

# Генерация полного пакета автоматизации
files = generate_full_automation_package(
    credentials=credentials,
    output_dir='./automation'
)

# Создаются файлы:
# - automation_script.py (основной скрипт)
# - cron_config.txt (для Linux)
# - docker-compose.yml (для контейнеризации)
# - .github/workflows/automation.yml (для GitHub Actions)
# - README_AUTOMATION.md (инструкции)

# Установка cron (Linux):
# crontab -e
# 0 9 * * * python /path/to/automation_script.py
```

---

## 🤖 AI Agent Features

### Auto-Analyze

AI-агент автоматически:

1. **Определяет приоритеты** - что анализировать дальше
2. **Находит аномалии** - резкие скачки, нулевые значения
3. **Предлагает deep dives** - дополнительные срезы
4. **Генерирует вопросы** - что еще изучить
5. **Находит возможности** - где оптимизировать

```python
agent = AnalyticsAgent(df)
analysis = agent.auto_analyze()

# Приоритетные deep dives
for suggestion in analysis['deep_dive_suggestions']:
    if suggestion['priority'] == 'HIGH':
        print(f"🔴 {suggestion['suggestion']}")
        print(f"   Причина: {suggestion['reason']}")
        print(f"   Действие: {suggestion['action']}")
```

### Custom Queries

Поддерживаемые паттерны:

```python
# Сравнение
agent.answer_custom_query("сравни video и banner")
agent.answer_custom_query("сравни advertisers по CTR")

# Фильтрация
agent.answer_custom_query("покажи продукты с высоким CTR")
agent.answer_custom_query("найди кампании с низким spend")

# Ранжирование
agent.answer_custom_query("топ 10 по конверсиям")
agent.answer_custom_query("лучшие креативы")
```

---

## 📈 Метрики и KPI

### Основные метрики для сравнения:

| Метрика | Описание | Формула |
|---------|----------|---------|
| **CTR** | Click-through rate | clicks / impressions |
| **CPM** | Cost per mille | (spend / impressions) * 1000 |
| **CPC** | Cost per click | spend / clicks |
| **Efficiency** | Эффективность бюджета | CTR / normalized_spend |
| **Conversion Rate** | Доля конверсий | conversions / clicks |

### Ранжирование:

```python
# Добавляются автоматически:
# - ctr_rank
# - spend_rank
# - efficiency_rank

summary = manager.get_comparison_summary(df)
print(summary[['advertiser_source', 'ctr', 'ctr_rank', 'efficiency_rank']])
```

---

## 🔧 Настройка

### Credentials Management

```python
# Вариант 1: Программно
credentials = [
    {"advertiser": "A", "api_key": "key1"},
    {"advertiser": "B", "api_key": "key2"}
]

# Вариант 2: Из environment
import os
credentials = [
    {"advertiser": "A", "api_key": os.getenv('API_KEY_A')},
    {"advertiser": "B", "api_key": os.getenv('API_KEY_B')}
]

# Вариант 3: Из файла
import json
with open('credentials.json', 'r') as f:
    credentials = json.load(f)
```

### Parallel Loading

```python
# Настройка параллелизма
manager = MultiAdvertiserManager(credentials=credentials)

# Parallel (быстрее для >2 advertisers)
df = manager.load_data(
    start_date='2024-01-01',
    end_date='2024-03-31',
    parallel=True  # ThreadPoolExecutor
)

# Sequential (надежнее для 1-2 advertisers)
df = manager.load_data(
    start_date='2024-01-01',
    end_date='2024-03-31',
    parallel=False
)
```

---

## ✅ Best Practices

1. **Добавьте минимум 2 advertisers** для сравнения
2. **Используйте параллельную загрузку** для >2 advertisers
3. **Валидируйте данные** после загрузки
4. **Запускайте AI-агент** для автоматических рекомендаций
5. **Генерируйте автоматизацию** для регулярных отчетов
6. **Сохраняйте credentials в .env** (не в коде!)

---

## 🆘 Troubleshooting

### Проблема: Данные несовместимы

**Решение:**
```python
validation = manager.validate_data_compatibility(df)
if validation['status'] == 'issues':
    for issue in validation['issues']:
        print(f"⚠️ {issue}")
```

### Проблема: Медленная загрузка

**Решение:**
- Используйте `parallel=True`
- Уменьшите период
- Проверьте `rate_limit_delay`

### Проблема: AI-агент не работает

**Решение:**
- Убедитесь, что в данных есть нужные колонки
- Проверьте, что `advertiser_source` присутствует
- Данные должны быть обработаны через DataProcessor

---

## 📚 Связанные файлы

- `multi_advertiser.py` - менеджер
- `analytics_agent.py` - AI-агент
- `automation_generator.py` - генератор автоматизации
- `google_export.py` - экспорт в Google
- `dashboard_multi.py` - UI

---

**Multi-Advertiser режим готов! 🚀**

Начните с `streamlit run dashboard_multi.py`


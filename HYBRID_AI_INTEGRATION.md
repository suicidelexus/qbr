# 🚀 Интеграция с Hybrid.ai DSP

## Быстрая настройка для Hybrid.ai

**Документация API:** https://docs.hybrid.ai/rest-api-3-0

---

## ⚡ Минимальная настройка

### Нужен только API Key!

**Шаг 1: Получите API Key в Hybrid.ai**

1. Войдите в https://hybrid.ai
2. Перейдите в **Settings → API Keys**
3. Нажмите **Generate New Key**
4. Скопируйте ключ

**Шаг 2: Настройте в Dashboard**

```bash
streamlit run dashboard.py
```

В браузере:
1. Раскройте **"🔑 API Credentials"**
2. Вставьте **API Key**
3. Нажмите **"🧪 Тест"**
4. Нажмите **"💾 Сохранить"**

**Готово!** API URL уже настроен на `https://api.hybrid.ai/v3`

---

## 📊 Hybrid.ai API Endpoints

Проект поддерживает все основные endpoints Hybrid.ai:

### 1. Statistics API
```python
from hybrid_ai_adapter import HybridAIClient

client = HybridAIClient()

# Статистика за период
stats = client.get_statistics(
    start_date='2024-01-01',
    end_date='2024-03-31',
    dimensions=['date', 'campaign', 'creative'],
    metrics=['impressions', 'clicks', 'spend', 'conversions'],
    group_by='day'
)
```

### 2. Campaigns API
```python
# Активные кампании
campaigns = client.get_campaigns_list(status='active')

# Кампании конкретного рекламодателя
campaigns = client.get_campaigns_list(advertiser_id=123)
```

### 3. Creatives API
```python
# Все креативы
creatives = client.get_creatives_list()

# Креативы конкретной кампании
creatives = client.get_creatives_list(campaign_id=456)
```

### 4. Placements API
```python
# Плейсменты
placements = client.get_placements(campaign_id=456)
```

### 5. DMP Segments API
```python
# DMP сегменты
segments = client.get_dmp_segments()
```

### 6. Realtime Statistics API
```python
# Realtime данные за последние 24 часа
realtime = client.get_realtime_stats(last_hours=24)

# Для конкретных кампаний
realtime = client.get_realtime_stats(
    campaign_ids=[123, 456, 789],
    last_hours=6
)
```

---

## 💡 Примеры использования

### Пример 1: Быстрая загрузка через Dashboard

```bash
# 1. Запустите Dashboard
streamlit run dashboard.py

# 2. Настройте API Key
# 3. Выберите "Загрузить из API"
# 4. Укажите период (например, 30 дней)
# 5. Нажмите "📥 Загрузить из API"
```

**Результат:** Данные из Hybrid.ai загружены и готовы к анализу!

---

### Пример 2: Анализ кампаний через CLI

```python
from hybrid_ai_adapter import HybridAIClient
from processing_layer import DataProcessor
from ai_layer import InsightGenerator

# Создаем клиент
client = HybridAIClient()

# Загружаем статистику за месяц
df = client.get_statistics(
    start_date='2024-03-01',
    end_date='2024-03-31',
    dimensions=['date', 'campaign'],
    metrics=['impressions', 'clicks', 'spend', 'conversions']
)

# Обрабатываем
processor = DataProcessor()
df = processor.calculate_derived_metrics(df)
df = processor.filter_significant(df)

# AI-анализ
gen = InsightGenerator(df)
results = gen.generate_full_analysis()

# Выводим результаты
print(results['tldr'])
for rec in results['recommendations']:
    print(f"• {rec}")
```

---

### Пример 3: Мониторинг в реальном времени

```python
from hybrid_ai_adapter import HybridAIClient

client = HybridAIClient()

# Получаем активные кампании
campaigns = client.get_campaigns_list(status='active')
campaign_ids = campaigns['id'].tolist()

# Realtime статистика
realtime = client.get_realtime_stats(
    campaign_ids=campaign_ids,
    last_hours=1
)

# Проблемные кампании
low_ctr = realtime[realtime['ctr'] < 0.001]
if not low_ctr.empty:
    print("⚠️ Кампании с низким CTR (последний час):")
    for _, row in low_ctr.iterrows():
        print(f"  - Campaign {row['campaign_id']}: CTR {row['ctr']:.3%}")
```

---

### Пример 4: Полный анализ с использованием main.py

```bash
# Через .env файл
echo "DSP_API_KEY=ваш_hybrid_ai_ключ" > .env

# Запуск анализа
python main.py api

# Результаты в папке output/
```

---

## 🔧 Расширенные возможности

### Использование Hybrid.ai адаптера

```python
from hybrid_ai_adapter import HybridAIClient

# Создание клиента с расширенными настройками
client = HybridAIClient(
    api_key='your_key',
    timeout=120,
    max_retries=5,
    rate_limit_delay=0.2
)

# Проверка подключения
if client.test_connection():
    print("✓ Подключено к Hybrid.ai")
```

### Пагинация для больших объемов

```python
# Загрузка всех кампаний с пагинацией
all_campaigns = []
offset = 0
limit = 100

while True:
    campaigns = client.get_campaigns_list(
        limit=limit,
        offset=offset
    )
    
    if campaigns.empty:
        break
    
    all_campaigns.append(campaigns)
    offset += limit

# Объединение
import pandas as pd
all_campaigns_df = pd.concat(all_campaigns, ignore_index=True)
```

---

## 📋 Mapping метрик Hybrid.ai

Hybrid.ai использует следующие названия метрик:

| Hybrid.ai | Наш проект |
|-----------|------------|
| `impressions` | `impressions` |
| `clicks` | `clicks` |
| `spend` | `TotalSum` |
| `conversions` | `post_click_conversions` |
| `revenue` | `revenue` |
| `ctr` | `ctr` (авто-расчет) |
| `cpc` | `cpc` (авто-расчет) |
| `cpm` | `cpm` (авто-расчет) |

**Автоматическая конвертация:** DataProcessor автоматически пересчитывает производные метрики.

---

## 🆘 Troubleshooting для Hybrid.ai

### Проблема: 401 Unauthorized

**Причина:** Неверный API Key

**Решение:**
1. Проверьте API Key в Hybrid.ai Settings → API Keys
2. Убедитесь, что ключ активен
3. Скопируйте ключ полностью (включая префикс)

### Проблема: 403 Forbidden

**Причина:** Недостаточно прав доступа

**Решение:**
1. Проверьте права API Key в Hybrid.ai
2. Убедитесь, что включен доступ к Statistics API
3. Свяжитесь с администратором для расширения прав

### Проблема: 429 Rate Limit

**Причина:** Превышен лимит запросов

**Решение:**
```python
# Увеличьте задержку между запросами
client = HybridAIClient(rate_limit_delay=1.0)
```

### Проблема: Нет данных за период

**Причина:** За выбранный период действительно нет данных

**Решение:**
1. Проверьте, что кампании были активны в этот период
2. Попробуйте другой период
3. Проверьте фильтры

---

## 📚 Документация

**Hybrid.ai официальная документация:**
- REST API 3.0: https://docs.hybrid.ai/rest-api-3-0

**Наша документация:**
- `hybrid_ai_adapter.py` - адаптер для Hybrid.ai
- `QUICKSTART_API.md` - быстрый старт
- `API_SETUP.md` - детальная настройка
- `DSP_API_GUIDE.md` - полное руководство по API

---

## ✅ Checklist для Hybrid.ai

Для успешной интеграции:

- [ ] Получен API Key из Hybrid.ai
- [ ] API Key вставлен в Dashboard или .env
- [ ] Проверено подключение (кнопка "🧪 Тест")
- [ ] Загружены тестовые данные
- [ ] Данные корректно отображаются
- [ ] AI-инсайты генерируются

---

## 🚀 Быстрый старт (3 шага)

```bash
# 1. Получите API Key в Hybrid.ai
# Settings → API Keys → Generate New Key

# 2. Запустите Dashboard
streamlit run dashboard.py

# 3. Настройте и загрузите
# Раскройте "🔑 API Credentials"
# Вставьте API Key
# Нажмите "🧪 Тест"
# Выберите "Загрузить из API"
```

**Готово!** Теперь анализируйте данные из Hybrid.ai! 🎉

---

## 💡 Советы для работы с Hybrid.ai

1. **Используйте dimensions** для детальной разбивки:
   - `['date', 'campaign', 'creative']` - максимум деталей
   - `['date', 'campaign']` - быстрая загрузка
   - `['campaign']` - агрегированные данные

2. **Фильтруйте на стороне API:**
   ```python
   stats = client.get_statistics(
       start_date='2024-01-01',
       end_date='2024-03-31',
       filters={
           'campaign_id': [123, 456],
           'status': 'active'
       }
   )
   ```

3. **Используйте realtime для мониторинга:**
   ```python
   # Проверка каждый час
   realtime = client.get_realtime_stats(last_hours=1)
   ```

4. **Комбинируйте с DMP сегментами:**
   ```python
   segments = client.get_dmp_segments()
   # Анализ по сегментам
   ```

---

**Hybrid.ai интеграция готова! Начните работу прямо сейчас! 🚀**


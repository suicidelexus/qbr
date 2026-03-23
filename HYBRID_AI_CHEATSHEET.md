# 📋 Hybrid.ai - Шпаргалка

## ⚡ Быстрый старт

```bash
# 1. Получите API Key в Hybrid.ai
# https://hybrid.ai → Settings → API Keys

# 2. Запустите Dashboard
streamlit run dashboard.py

# 3. Вставьте API Key и нажмите "Тест"
# 4. Выберите "Загрузить из API"
# 5. Готово!
```

## 🔑 API Key

**Где получить:**
- https://hybrid.ai
- Settings → API Keys
- Generate New Key

**API URL:** `https://api.hybrid.ai/v3` (уже настроен)

## 📊 Основные команды

### Создание клиента
```python
from hybrid_ai_adapter import HybridAIClient
client = HybridAIClient()
```

### Статистика
```python
# За период
stats = client.get_statistics(
    start_date='2024-01-01',
    end_date='2024-03-31',
    dimensions=['date', 'campaign'],
    metrics=['impressions', 'clicks', 'spend']
)

# За последние N дней
stats = client.get_last_n_days(days=30)
```

### Кампании
```python
campaigns = client.get_campaigns_list(status='active')
```

### Креативы
```python
creatives = client.get_creatives_list(campaign_id=123)
```

### Realtime
```python
realtime = client.get_realtime_stats(last_hours=24)
```

### DMP
```python
segments = client.get_dmp_segments()
```

## 🎯 Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/statistics` | `get_statistics()` | Статистика |
| `/campaigns` | `get_campaigns_list()` | Кампании |
| `/creatives` | `get_creatives_list()` | Креативы |
| `/placements` | `get_placements()` | Плейсменты |
| `/dmp/segments` | `get_dmp_segments()` | DMP |
| `/statistics/realtime` | `get_realtime_stats()` | Realtime |

## 📝 Dimensions

```python
dimensions=[
    'date',       # Дата
    'campaign',   # Кампания
    'creative',   # Креатив
    'placement',  # Плейсмент
    'format',     # Формат
    'device'      # Устройство
]
```

## 📈 Metrics

```python
metrics=[
    'impressions',  # Показы
    'clicks',       # Клики
    'spend',        # Расход
    'conversions',  # Конверсии
    'revenue'       # Выручка
]
```

## 🆘 Ошибки

| Код | Причина | Решение |
|-----|---------|---------|
| 401 | Неверный ключ | Проверить API Key |
| 403 | Нет прав | Проверить права ключа |
| 429 | Rate limit | Увеличить delay |

## 💡 Примеры

### Мониторинг
```python
# Активные кампании
camps = client.get_campaigns_list(status='active')

# Их статистика за час
stats = client.get_realtime_stats(
    campaign_ids=camps['id'].tolist(),
    last_hours=1
)
```

### Анализ с AI
```python
from ai_layer import InsightGenerator

stats = client.get_last_n_days(30)
gen = InsightGenerator(stats)
results = gen.generate_full_analysis()
print(results['tldr'])
```

### Dashboard
```
1. streamlit run dashboard.py
2. API Key → Тест → Сохранить
3. "Загрузить из API" → 30 дней
4. AI-инсайты
```

## 📚 Документация

- **HYBRID_AI_INTEGRATION.md** - полный гайд
- **QUICKSTART_API.md** - быстрый старт
- https://docs.hybrid.ai/rest-api-3-0 - официальная

## ✅ Checklist

- [ ] Получен API Key из Hybrid.ai
- [ ] Ключ вставлен в Dashboard
- [ ] Тест подключения успешен
- [ ] Данные загружаются

**Готово! 🚀**


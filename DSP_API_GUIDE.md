# 🔌 DSP API Integration Guide

## Полное руководство по интеграции с DSP платформой

---

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Конфигурация](#конфигурация)
3. [Аутентификация](#аутентификация)
4. [Доступные Endpoints](#доступные-endpoints)
5. [Примеры использования](#примеры-использования)
6. [Обработка ошибок](#обработка-ошибок)
7. [Best Practices](#best-practices)

---

## 🚀 Быстрый старт

### 1. Настройка credentials

Создайте файл `.env` в корне проекта:

```env
DSP_API_URL=https://api.your-dsp-platform.com/v1
DSP_API_KEY=your_api_key_here
DSP_CLIENT_ID=your_client_id_here
```

### 2. Тест подключения

```python
from data_layer import DSPClient

# Создание клиента
client = DSPClient()

# Проверка подключения
if client.test_connection():
    print("✓ Подключение успешно!")
else:
    print("✗ Ошибка подключения")
```

### 3. Получение данных

```python
# Загрузка отчета за последние 30 дней
df = client.get_last_n_days(days=30)

# Или за конкретный период
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-03-31'
)
```

---

## ⚙️ Конфигурация

### Параметры клиента

```python
client = DSPClient(
    api_url='https://api.dsp-platform.com/v1',  # URL API
    api_key='your_api_key',                      # API ключ
    client_id='your_client_id',                  # ID клиента
    timeout=60,                                   # Таймаут запросов (сек)
    max_retries=3,                                # Попытки при ошибках
    rate_limit_delay=0.1                          # Задержка между запросами
)
```

### Переменные окружения

| Переменная | Описание | Обязательно |
|-----------|----------|-------------|
| `DSP_API_URL` | URL DSP API | Да |
| `DSP_API_KEY` | API ключ для аутентификации | Да |
| `DSP_CLIENT_ID` | ID клиента (если требуется) | Нет |

---

## 🔐 Аутентификация

### Bearer Token (рекомендуется)

API использует Bearer токен в заголовке:

```
Authorization: Bearer YOUR_API_KEY
```

### Получение API ключа

1. Войдите в DSP платформу
2. Перейдите в **Settings → API Keys**
3. Нажмите **Generate New Key**
4. Скопируйте ключ в `.env` файл

**⚠️ Важно:** Никогда не коммитьте API ключи в git!

---

## 📡 Доступные Endpoints

### 1. Reports (Отчеты)

Основной endpoint для получения аналитических данных.

```python
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-03-31',
    metrics=['impressions', 'clicks', 'ctr', 'TotalSum'],
    dimensions=['date', 'advertiser', 'campaign'],
    filters={
        'advertiser': 'Advertiser A',
        'campaign_status': 'active'
    },
    use_pagination=True  # Автоматическая пагинация
)
```

**Параметры:**
- `start_date` - дата начала (YYYY-MM-DD)
- `end_date` - дата окончания (YYYY-MM-DD)
- `metrics` - список метрик (по умолчанию все из config)
- `dimensions` - разрезы данных
- `filters` - фильтры
- `use_pagination` - использовать пагинацию для больших объемов

**Возвращает:** DataFrame с данными

---

### 2. Campaigns (Кампании)

Получение списка кампаний.

```python
campaigns = client.get_campaigns(
    advertiser_id='adv_123',
    status='active',
    start_date='2024-01-01',
    end_date='2024-03-31'
)
```

**Параметры:**
- `advertiser_id` - ID рекламодателя
- `status` - статус (active, paused, archived)
- `start_date` - дата начала
- `end_date` - дата окончания

**Возвращает:** DataFrame с кампаниями

---

### 3. Creatives (Креативы)

Получение креативов.

```python
creatives = client.get_creatives(
    campaign_id='camp_456',
    format='video',
    status='active'
)
```

**Параметры:**
- `campaign_id` - ID кампании
- `format` - формат (video, banner, native)
- `status` - статус

**Возвращает:** DataFrame с креативами

---

### 4. Audiences (Аудитории)

Получение DMP аудиторий.

```python
audiences = client.get_audiences()
```

**Возвращает:** DataFrame с аудиториями

---

### 5. Advertisers (Рекламодатели)

Получение списка рекламодателей.

```python
advertisers = client.get_advertisers()
```

**Возвращает:** DataFrame с рекламодателями

---

## 💡 Примеры использования

### Пример 1: Полный анализ за месяц

```python
from data_layer import DataLoader
from processing_layer import DataProcessor
from ai_layer import InsightGenerator

# Загрузка данных
loader = DataLoader()
df = loader.dsp_client.get_report(
    start_date='2024-03-01',
    end_date='2024-03-31',
    dimensions=['date', 'advertiser', 'campaign', 'format']
)

# Обработка
processor = DataProcessor()
df = processor.calculate_derived_metrics(df)
df = processor.filter_significant(df)

# AI-анализ
gen = InsightGenerator(df)
results = gen.generate_full_analysis()

# Вывод
print(results['tldr'])
for rec in results['recommendations']:
    print(f"• {rec}")
```

---

### Пример 2: Мониторинг активных кампаний

```python
from data_layer import DSPClient
import pandas as pd

client = DSPClient()

# Получаем активные кампании
campaigns = client.get_campaigns(status='active')

# Получаем performance за последние 7 дней
df = client.get_last_n_days(
    days=7,
    dimensions=['campaign'],
    filters={
        'campaign_id': campaigns['id'].tolist()
    }
)

# Находим проблемные кампании
low_ctr = df[df['ctr'] < 0.001]
print("Кампании с низким CTR:")
print(low_ctr[['campaign', 'ctr', 'impressions']])
```

---

### Пример 3: Сравнение креативов

```python
client = DSPClient()

# Получаем креативы кампании
creatives = client.get_creatives(campaign_id='camp_123')

# Получаем performance каждого креатива
df = client.get_report(
    start_date='2024-03-01',
    end_date='2024-03-31',
    dimensions=['creative_id'],
    filters={
        'creative_id': creatives['id'].tolist()
    }
)

# Сортируем по CTR
best_creatives = df.sort_values('ctr', ascending=False)
print("Топ-5 креативов по CTR:")
print(best_creatives.head()[['creative_id', 'ctr', 'impressions', 'clicks']])
```

---

### Пример 4: Автоматическая загрузка в main.py

```python
# В main.py уже поддерживается API режим:
python main.py api

# Или программно:
from main import analyze_dsp_data

results = analyze_dsp_data(
    source='api',
    start_date='2024-01-01',
    end_date='2024-03-31',
    output_dir='./output'
)
```

---

## 🛡️ Обработка ошибок

### Автоматический Retry

Клиент автоматически повторяет запросы при ошибках:

- **429** (Rate Limit) - повтор с backoff
- **500, 502, 503, 504** (Server errors) - повтор с backoff
- **Timeout** - повтор запроса

**Настройка:**
```python
client = DSPClient(
    max_retries=5,           # 5 попыток
    rate_limit_delay=0.5     # 0.5 сек задержка
)
```

---

### Обработка ошибок вручную

```python
from data_layer import DSPClient

client = DSPClient()

try:
    df = client.get_report(
        start_date='2024-01-01',
        end_date='2024-03-31'
    )
    
    if df.empty:
        print("Нет данных за указанный период")
    else:
        print(f"Загружено {len(df)} строк")
        
except requests.exceptions.HTTPError as e:
    print(f"HTTP ошибка: {e.response.status_code}")
    
except requests.exceptions.Timeout:
    print("Превышен таймаут запроса")
    
except Exception as e:
    print(f"Неожиданная ошибка: {e}")
```

---

## 🎯 Best Practices

### 1. Используйте пагинацию для больших объемов

```python
# Автоматическая пагинация
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-12-31',
    use_pagination=True  # Загрузит все страницы
)
```

### 2. Кэшируйте справочники

```python
# Загрузите один раз и переиспользуйте
advertisers = client.get_advertisers()
campaigns = client.get_campaigns()

# Сохраните локально
advertisers.to_csv('cache/advertisers.csv')
```

### 3. Ограничивайте диапазоны дат

```python
# Плохо - может быть слишком много данных
df = client.get_report(
    start_date='2020-01-01',
    end_date='2024-12-31'
)

# Хорошо - разбивайте на периоды
import pandas as pd
from datetime import datetime, timedelta

def load_by_months(start, end):
    current = datetime.strptime(start, '%Y-%m-%d')
    end_dt = datetime.strptime(end, '%Y-%m-%d')
    
    dfs = []
    while current < end_dt:
        month_end = min(
            current + timedelta(days=30),
            end_dt
        )
        
        df = client.get_report(
            start_date=current.strftime('%Y-%m-%d'),
            end_date=month_end.strftime('%Y-%m-%d')
        )
        dfs.append(df)
        
        current = month_end
    
    return pd.concat(dfs, ignore_index=True)
```

### 4. Используйте фильтры на стороне API

```python
# Плохо - загружаем все, фильтруем локально
df = client.get_report(start_date='2024-01-01', end_date='2024-12-31')
df = df[df['advertiser'] == 'Advertiser A']

# Хорошо - фильтруем на стороне API
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-12-31',
    filters={'advertiser': 'Advertiser A'}
)
```

### 5. Проверяйте подключение перед запуском

```python
client = DSPClient()

if not client.test_connection():
    print("Ошибка подключения к API")
    exit(1)

# Продолжаем работу
df = client.get_last_n_days(30)
```

---

## 🔧 Troubleshooting

### Проблема: 401 Unauthorized

**Причина:** Неверный API ключ

**Решение:**
```bash
# Проверьте .env файл
cat .env | grep DSP_API_KEY

# Убедитесь, что ключ актуален
# Сгенерируйте новый ключ в DSP платформе
```

---

### Проблема: 429 Too Many Requests

**Причина:** Превышен rate limit

**Решение:**
```python
# Увеличьте задержку между запросами
client = DSPClient(rate_limit_delay=1.0)  # 1 секунда

# Или уменьшите параллельность
```

---

### Проблема: 504 Gateway Timeout

**Причина:** Запрос слишком большой или API недоступен

**Решение:**
```python
# Уменьшите диапазон дат
# Используйте пагинацию
# Проверьте статус API
```

---

## 📊 Форматы данных

### Структура ответа Reports endpoint

```json
{
  "rows": [
    {
      "date": "2024-03-01",
      "advertiser": "Advertiser A",
      "campaign": "Campaign 1",
      "impressions": 100000,
      "clicks": 250,
      "ctr": 0.0025,
      "TotalSum": 600.00
    }
  ],
  "total": 1000,
  "page": 1,
  "page_size": 100,
  "has_more": true
}
```

---

## 🔄 Интеграция с Pipeline

### Пример ETL pipeline

```python
from data_layer import DSPClient
from processing_layer import DataProcessor
from ai_layer import InsightGenerator
import schedule
import time

def daily_report():
    """Ежедневный отчет"""
    client = DSPClient()
    
    # Загрузка данных за вчера
    df = client.get_last_n_days(days=1)
    
    # Обработка
    processor = DataProcessor()
    df = processor.calculate_derived_metrics(df)
    
    # Анализ
    gen = InsightGenerator(df)
    results = gen.generate_full_analysis()
    
    # Отправка отчета (email, Slack, etc.)
    send_report(results)

# Запуск каждый день в 9:00
schedule.every().day.at("09:00").do(daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 📚 Дополнительные ресурсы

- **README.md** - общая документация проекта
- **ARCHITECTURE.md** - архитектура системы
- **QUICKSTART.md** - быстрый старт
- **data_layer.py** - исходный код DSPClient

---

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте `.env` файл
2. Запустите `client.test_connection()`
3. Проверьте логи ошибок
4. Обратитесь к документации DSP платформы

---

**Версия:** 2.0.0
**Дата:** 2026-03-23
**Статус:** Production Ready

🚀 **Готово к использованию!**


# 📋 DSP API - Шпаргалка

## ⚡ Быстрый старт

### Способ 1: Через Dashboard UI (рекомендуется) ✨
```bash
# 1. Запустить Dashboard
streamlit run dashboard.py

# 2. В sidebar:
#    - Раскрыть "🔑 API Credentials"
#    - Ввести API URL и API Key
#    - Нажать "🧪 Тест"
#    - Нажать "💾 Сохранить"

# 3. Выбрать "Загрузить из API"
# 4. Готово!
```

### Способ 2: Через .env файл
```bash
# 1. Настройка
cp .env.example .env
nano .env  # добавить DSP_API_KEY

# 2. Тест
python test_api.py

# 3. Использование
python main.py api
```

## 🌐 Dashboard UI

### Настройка через интерфейс
```
Sidebar → "🔑 API Credentials"
├─ API URL: [____________]
├─ API Key: [••••••••••••]
├─ Client ID: [_________]
├─ [💾 Сохранить] [🧪 Тест]
└─ [💾 Сохранить в .env]
```

### Загрузка данных
```
Sidebar → "📥 Загрузка данных"
└─ "Загрузить из API"
   ├─ Режим 1: Последние N дней
   └─ Режим 2: Конкретный период
```

## 🔑 Основные команды

### Создание клиента
```python
from data_layer import DSPClient
client = DSPClient()
```

### Загрузка данных
```python
# За последние N дней
df = client.get_last_n_days(days=30)

# За период
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-03-31'
)
```

### Кампании
```python
campaigns = client.get_campaigns(status='active')
```

### Креативы
```python
creatives = client.get_creatives(format='video')
```

### Тест подключения
```python
client.test_connection()  # True/False
```

## 📊 Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/reports` | `get_report()` | Аналитика |
| `/campaigns` | `get_campaigns()` | Кампании |
| `/creatives` | `get_creatives()` | Креативы |
| `/audiences` | `get_audiences()` | DMP |
| `/advertisers` | `get_advertisers()` | Рекламодатели |

## 🛠️ Параметры клиента

```python
DSPClient(
    api_url='...',              # URL API
    api_key='...',              # Ключ
    timeout=60,                 # Таймаут (сек)
    max_retries=3,              # Попыток
    rate_limit_delay=0.1        # Задержка (сек)
)
```

## 📝 Примеры

### Базовый отчет
```python
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-01-31',
    metrics=['impressions', 'clicks', 'ctr'],
    dimensions=['date', 'campaign'],
    filters={'status': 'active'}
)
```

### С пагинацией
```python
df = client.get_report(
    start_date='2024-01-01',
    end_date='2024-12-31',
    use_pagination=True  # Загрузит все
)
```

### Полный анализ
```python
from data_layer import DataLoader
from ai_layer import InsightGenerator

loader = DataLoader()
df = loader.dsp_client.get_last_n_days(30)

gen = InsightGenerator(df)
results = gen.generate_full_analysis()
print(results['tldr'])
```

## 🆘 Ошибки

| Код | Причина | Решение |
|-----|---------|---------|
| 401 | Неверный ключ | Проверить .env |
| 429 | Rate limit | Увеличить delay |
| 504 | Таймаут | Пагинация |

## 📚 Документация

- **API_SETUP.md** - настройка
- **DSP_API_GUIDE.md** - полный гайд
- **api_examples.py** - примеры
- **test_api.py** - тест

## 🧪 Тестирование

```bash
# Подключение
python test_api.py

# Примеры
python api_examples.py

# Полный анализ
python main.py api
```

## 💡 Best Practices

✅ Используй пагинацию для больших периодов  
✅ Кэшируй справочники (campaigns, advertisers)  
✅ Обрабатывай ошибки явно  
✅ Используй фильтры на стороне API  
✅ Проверяй `test_connection()` перед запуском  

## 🚀 Готово!

Все что нужно для работы с DSP API.


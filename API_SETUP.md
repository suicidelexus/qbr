# 🔧 Быстрая настройка DSP API

## Шаг 1: Получите API credentials

### В DSP платформе:

1. Войдите в свою DSP платформу
2. Перейдите в **Settings → API Access** (или **API Keys**)
3. Нажмите **Generate New API Key**
4. Сохраните полученные данные:
   - API URL
   - API Key
   - Client ID (если есть)

---

## Шаг 2: Настройте .env файл

```bash
# Скопируйте пример
cp .env.example .env

# Откройте для редактирования
nano .env
# или
notepad .env
```

Заполните данные:

```env
DSP_API_URL=https://api.your-dsp.com/v1
DSP_API_KEY=your_actual_api_key_here
DSP_CLIENT_ID=your_client_id
```

**⚠️ Важно:** Никогда не коммитьте .env в git!

---

## Шаг 3: Проверьте подключение

```bash
python -c "from data_layer import DSPClient; DSPClient().test_connection()"
```

**Ожидаемый результат:**
```
[OK] Подключение к DSP API успешно
```

---

## Шаг 4: Загрузите тестовые данные

```python
from data_layer import DSPClient

client = DSPClient()

# Данные за последние 7 дней
df = client.get_last_n_days(days=7)

print(f"Загружено {len(df)} строк")
print(df.head())
```

---

## Шаг 5: Запустите полный анализ

```bash
python main.py api
```

Или программно:

```python
from main import analyze_dsp_data

results = analyze_dsp_data(
    source='api',
    start_date='2024-01-01',
    end_date='2024-03-31'
)
```

---

## Распространенные проблемы

### 1. Ошибка 401 Unauthorized

**Причина:** Неверный API key

**Решение:**
- Проверьте .env файл
- Убедитесь, что ключ актуален
- Сгенерируйте новый ключ в DSP платформе

### 2. Ошибка Connection Refused

**Причина:** Неверный URL или API недоступен

**Решение:**
- Проверьте DSP_API_URL
- Убедитесь, что добавили `/v1` или нужную версию API
- Проверьте доступность API: `curl https://api.your-dsp.com/v1/health`

### 3. Ошибка 429 Rate Limit

**Причина:** Превышен лимит запросов

**Решение:**
```python
# Увеличьте задержку между запросами
client = DSPClient(rate_limit_delay=1.0)
```

---

## Дополнительная настройка

### Кастомные параметры

```python
from data_layer import DSPClient

client = DSPClient(
    api_url='https://custom-api.com',
    api_key='custom_key',
    timeout=120,          # 2 минуты таймаут
    max_retries=5,        # 5 попыток при ошибках
    rate_limit_delay=0.5  # 0.5 сек между запросами
)
```

---

## Примеры использования

См. подробные примеры в:
- **DSP_API_GUIDE.md** - полное руководство
- **api_examples.py** - 9 примеров использования

Запуск примеров:
```bash
python api_examples.py
```

---

## Следующие шаги

1. ✅ Настроили API подключение
2. ✅ Проверили работоспособность
3. ⬜ Изучите **DSP_API_GUIDE.md**
4. ⬜ Запустите **api_examples.py**
5. ⬜ Интегрируйте в свой workflow

---

**Готово! API настроен и работает 🚀**


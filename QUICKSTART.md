# 🚀 Quick Start Guide - DSP Analytics Platform

## Быстрый старт за 3 минуты

### 1️⃣ Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2️⃣ Запуск демо

**Вариант A: CLI (консоль)**
```bash
python main.py demo
```

**Вариант B: Web Dashboard (браузер)**
```bash
streamlit run dashboard.py
```

### 3️⃣ Результаты

#### CLI режим создает:
```
output/
├── report.md              # Markdown отчет с инсайтами
├── results.json           # JSON данные
└── charts/                # 6 интерактивных HTML графиков
    ├── advertisers.html
    ├── budget_optimization.html
    ├── correlation.html
    ├── dmp.html
    ├── dynamics.html
    └── media_split.html
```

#### Web Dashboard открывает:
- Интерактивный интерфейс на http://localhost:8501
- 5 вкладок с аналитикой
- AI-инсайты в реальном времени

---

## 📋 Основные команды

### Анализ своих данных

**CSV файл:**
```bash
python main.py your_data.csv
```

**Excel файл:**
```bash
python main.py your_data.xlsx
```

**DSP API:**
```bash
python main.py api
```

### Запуск тестов

```bash
python tests.py
```

**Результат:** 15 тестов за ~0.2 секунды

---

## 📊 Требования к данным

### Обязательные колонки:
- `date` - дата (YYYY-MM-DD)
- `advertiser` - рекламодатель
- `impressions` - показы
- `clicks` - клики
- `TotalSum` - общие расходы

### Опциональные колонки:
- `product` - продукт/категория
- `format` - формат (video/banner/native)
- `viewability` - viewability (0-1)
- `frequency` - frequency
- `vtr` - video completion rate
- `post_click_conversions` - конверсии
- `revenue` - выручка

---

## 🎯 Что получаете

### Автоматический анализ:
✅ Сравнение advertisers  
✅ Анализ продуктов  
✅ Медиасплит по форматам  
✅ Динамика метрик  
✅ DMP эффективность  
✅ Frequency анализ  
✅ Корреляции метрик  
✅ Оптимизация бюджета  

### AI-инсайты:
✅ Лидеры и аутсайдеры  
✅ Проблемные зоны  
✅ Рекомендации  
✅ Гипотезы для тестов  

### Визуализация:
✅ 7 типов интерактивных графиков  
✅ Экспорт в HTML  
✅ Готово для презентаций  

---

## 💡 Примеры использования

### Пример 1: Быстрый анализ CSV

```bash
python main.py campaign_data.csv
```

Результат: Полный отчет в `./output/report.md`

### Пример 2: Интерактивная работа

```bash
streamlit run dashboard.py
```

1. Нажать "Сгенерировать демо данные"
2. Изучить вкладки
3. Нажать "Сгенерировать AI-инсайты"

### Пример 3: Программное использование

```python
from data_layer import DataLoader
from processing_layer import AnalysisEngine
from ai_layer import InsightGenerator

# Загрузка
loader = DataLoader()
df = loader.load_from_csv('data.csv')

# Анализ
engine = AnalysisEngine(df)
advertisers = engine.compare_advertisers()
budget_opt = engine.budget_optimization()

# AI-инсайты
gen = InsightGenerator(df)
results = gen.generate_full_analysis()

print(results['tldr'])
for rec in results['recommendations']:
    print(f"✓ {rec}")
```

---

## 🔧 Настройка

### Конфигурация через .env

Создайте файл `.env`:

```env
DSP_API_URL=https://api.dsp-platform.com/v1
DSP_API_KEY=your_api_key_here
DSP_CLIENT_ID=your_client_id_here
```

### Изменение бенчмарков

Отредактируйте `config.py`:

```python
MIN_IMPRESSIONS = 1000
CTR_BENCHMARK = 0.001  # 0.1%
VTR_BENCHMARK = 0.25   # 25%
VIEWABILITY_BENCHMARK = 0.70  # 70%
```

---

## 🆘 Частые проблемы

### Проблема: Ошибка импорта модулей
**Решение:**
```bash
pip install -r requirements.txt
```

### Проблема: Пустые графики
**Решение:** Проверьте, что в данных есть обязательные колонки

### Проблема: Streamlit не запускается
**Решение:**
```bash
pip install streamlit
streamlit run dashboard.py
```

### Проблема: Кодировка в CSV
**Решение:** Сохраните CSV в UTF-8

---

## 📚 Дополнительно

- **README.md** - полная документация
- **ARCHITECTURE.md** - описание архитектуры
- **STATUS.md** - текущий статус и roadmap
- **tests.py** - unit тесты

---

## 🎓 Следующие шаги

1. ✅ Запустите демо
2. ✅ Загрузите свои данные
3. ✅ Изучите отчеты
4. ✅ Настройте под свои нужды
5. ✅ Интегрируйте в workflow

---

## 💬 Поддержка

- Документация: `README.md`
- Архитектура: `ARCHITECTURE.md`
- Тесты: `python tests.py`
- Примеры: `python main.py demo`

---

**Готово! Начните с `python main.py demo` или `streamlit run dashboard.py`**

🚀 DSP Analytics Platform - AI-powered solution


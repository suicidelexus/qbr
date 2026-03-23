# ⚡ Быстрый старт - Hybrid.ai DSP

## 🎯 Нужен только API Key от Hybrid.ai!

**Документация:** https://docs.hybrid.ai/rest-api-3-0

### Шаг 1: Получите API Key

1. Войдите в **https://hybrid.ai**
2. **Settings → API Keys**
3. **Generate New Key**
4. Скопируйте ключ

### Шаг 2: Вставьте в Dashboard

```bash
# Запустите Dashboard
streamlit run dashboard.py
```

В браузере:
1. Раскройте **"🔑 API Credentials"**
2. Вставьте **API Key** от Hybrid.ai
3. Нажмите **"🧪 Тест"**
4. Если ✓ успешно - нажмите **"💾 Сохранить"**

**API URL уже настроен на Hybrid.ai** (`https://api.hybrid.ai/v3`)

### Шаг 3: Загрузите данные

1. Выберите **"Загрузить из API"**
2. Укажите период (например, 30 дней)
3. Нажмите **"📥 Загрузить из API"**

**Готово!** Данные из Hybrid.ai загружены! 🎉

---

## ❓ А что насчет API URL?

**Не нужен!** Используется автоматически.

Меняйте только если:
- В документации вашей DSP явно указан другой URL
- Тест показывает ошибку 404

См. подробнее: [API_URL_EXPLAINED.md](API_URL_EXPLAINED.md)

---

## 📝 Альтернатива: через .env

```bash
# Создайте .env файл
echo "DSP_API_KEY=ваш_ключ_здесь" > .env

# Проверьте
python test_api.py

# Запустите
python main.py api
```

---

## 🆘 Проблемы?

**401 Unauthorized:**
→ Неверный API Key (проверьте ключ)

**404 Not Found:**
→ Возможно нужен другой API URL (см. документацию)

**Connection Error:**
→ Проверьте интернет и доступность платформы

---

**Все просто!** Только API Key и все работает! 🚀


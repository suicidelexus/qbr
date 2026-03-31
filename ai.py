"""
LLM client — OpenAI-compatible SDK, works with OpenAI / Mistral / any proxy
"""
import json
from typing import Optional, Generator

import config

SYSTEM_ANALYST = (
    "Ты — senior медиа-аналитик агентства digital-рекламы. "
    "НЕ описывай данные — находи инсайты, объясняй причины, давай конкретные рекомендации. "
    "Пиши на русском. Формат: markdown. Всегда указывай цифры."
)


def _df_to_text(df, max_rows: int = 40) -> str:
    if df.empty:
        return "(нет данных)"
    df = df.copy()
    for col in df.columns:
        if col == 'ctr':
            df[col] = df[col].apply(lambda x: f"{x:.2%}" if isinstance(x, float) else x)
        elif col == 'viewability':
            df[col] = df[col].apply(lambda x: f"{x:.0%}" if isinstance(x, float) else x)
        elif col == 'vtr':
            df[col] = df[col].apply(lambda x: f"{x:.0%}" if isinstance(x, float) else x)
    return "\n".join([
        f"Колонки: {list(df.columns)}",
        f"Строк: {len(df)}",
        f"--- Данные ---\n{df.head(max_rows).to_string(index=False)}",
    ])


class LLMClient:
    def __init__(self, api_key: str, provider: str = "OpenAI",
                 model: Optional[str] = None, base_url: Optional[str] = None):
        from openai import OpenAI
        cfg = config.LLM_PROVIDERS.get(provider, {})
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url or cfg.get('base_url'),
        )
        self.model = model or cfg.get('default_model', 'gpt-4o-mini')

    def chat(self, user_msg: str, system: str = SYSTEM_ANALYST,
             max_tokens: int = 3000) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content

    def stream_chat(self, user_msg: str, system: str = SYSTEM_ANALYST,
                    max_tokens: int = 3000) -> Generator[str, None, None]:
        """Streaming version — yields text chunks as they arrive."""
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def detect_columns(self, col_names: list, sample_json: str) -> dict:
        standard_keys = list(config.STANDARD_COLS.keys())
        prompt = (
            f"Колонки таблицы: {col_names}\n\n"
            f"Первые 3 строки данных:\n{sample_json}\n\n"
            f"Стандартные поля: {standard_keys}\n\n"
            "Верни ТОЛЬКО JSON вида {{\"original_col\": \"standard_field\"}} "
            "только для колонок которые точно соответствуют стандартному полю. "
            "Никакого текста кроме JSON."
        )
        raw = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600, temperature=0,
        ).choices[0].message.content.strip()
        start, end = raw.find('{'), raw.rfind('}') + 1
        try:
            return json.loads(raw[start:end]) if start >= 0 else {}
        except json.JSONDecodeError:
            return {}

    def analyze(self, dfs: dict, prompt_type: str, custom_question: str = '') -> str:
        user_msg, system = self._build_prompt(dfs, prompt_type, custom_question)
        return self.chat(user_msg, system=system, max_tokens=3000)

    def stream_analyze(self, dfs: dict, prompt_type: str,
                       custom_question: str = '') -> Generator[str, None, None]:
        user_msg, system = self._build_prompt(dfs, prompt_type, custom_question)
        yield from self.stream_chat(user_msg, system=system, max_tokens=3000)

    def _build_prompt(self, dfs: dict, prompt_type: str, custom_question: str = ''):
        parts = []
        for name, df in dfs.items():
            if df is not None and not df.empty:
                parts.append(f"=== {name} ===\n{_df_to_text(df)}")
        data_text = "\n\n".join(parts) if parts else "(нет данных)"

        prompts = {
            "insights": "Найди неочевидные инсайты, аномалии, корреляции и паттерны. Что выбивается из нормы? Что скрыто в данных?",
            "trends": "Проанализируй динамику. Тренды, точки перелома, сравнение периодов, прогноз при текущих трендах.",
            "budget": "Оцени эффективность бюджета. Кто даёт лучший ROI? Куда перераспределить? Формат: Действие → Обоснование → Ожидаемый результат.",
            "summary": "Напиши краткое Executive Summary на 300–400 слов. Главный результат, 5–7 ключевых цифр, одна рекомендация.",
            "custom": f"Вопрос пользователя: {custom_question}\n\nОтветь на основе предоставленных данных. Будь конкретен, ссылайся на цифры.",
        }

        system = SYSTEM_ANALYST
        user_msg = prompts.get(prompt_type, prompts["custom"]) + f"\n\nДанные:\n{data_text}"
        return user_msg, system


def _prompt_qbr() -> str:
    return """Составь профессиональный Quarterly Business Review (QBR) по следующей структуре:

## 1. Executive Summary
3–4 предложения: главный итог + 3 ключевые цифры + главный вывод для клиента.

## 2. Обзор периода
- Период, общий бюджет, количество рекламодателей
- Сравнение с предыдущим периодом: бюджет Δ%, показы Δ%, клики Δ% (если есть данные)
- ТОП-3 рекламодателя с долями бюджета %

## 3. Ключевые метрики
Для каждого рекламодателя: Impressions | Clicks | CTR | CPM | CPC | Бюджет
Рядом: ✅ выше бенчмарка (CTR>0.1%, Viewability>70%, VTR>25%) или ⚠️ ниже.

## 4. Динамика квартала
Тренд по месяцам: CTR, CPM, бюджет. Лучший и худший период с объяснением.

## 5. Лидеры и аутсайдеры
**Лидеры (ТОП-3):** [Рекламодатель] — CTR X.XX%, что делает правильно
**Аутсайдеры:** [Рекламодатель] — CTR X.XX% (норма 0.1%), конкретная проблема

## 6. Эффективность форматов
Какой формат/banner_type дал лучший CTR/CPM. Рекомендации по распределению бюджета.

## 7. Зоны внимания
3 проблемы по формату: 🔴 [Проблема]: [цифра] vs норма [цифра] → причина → потери

## 8. Рекомендации
Минимум 4, формат строго:
**[Действие]** → *Почему*: обоснование с цифрами → *Ожидаемый результат*: конкретный KPI

## 9. План действий
5 пунктов с приоритетом [СРОЧНО / ВАЖНО / ПЛАНОВО] и сроком.

Пиши на русском. Только факты и цифры — никакой воды."""

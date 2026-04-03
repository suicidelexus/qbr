"""
LLM client — OpenAI-compatible SDK, works with OpenAI / Mistral / any proxy
"""
import json
from typing import Optional, Generator

import config

SYSTEM_ANALYST = (
    "Ты — senior медиа-аналитик агентства digital-рекламы. "
    "НЕ описывай данные — находи инсайты, объясняй причины, давай конкретные рекомендации. "
    "Пиши на русском. Формат: markdown. Всегда указывай цифры.\n\n"
    "## Бизнес-правила форматов\n"
    "- VTR (view-through rate, досматриваемость) применим ТОЛЬКО к формату Video. "
    "Для формата Display значение VTR = 0 — это норма, НЕ аномалия, не упоминай его как проблему.\n"
    "- НИКОГДА не сравнивай метрики между форматами Video и Display напрямую: "
    "CTR Video vs CTR Display, VTR Display vs VTR Video и т.п. — это некорректное сравнение.\n"
    "- Display сравнивай только с Display, Video — только с Video.\n"
    "- Viewability применима к Display; для Video ориентируйся на VTR.\n"
    "Если в данных присутствуют оба формата — анализируй каждый отдельно, со своими бенчмарками.\n"
    "- Анализируй ТОЛЬКО данные из предоставленного файла — это внутренняя платформа. "
    "НИКОГДА не упоминай сторонние платформы: TikTok, Instagram, Facebook, YouTube, ВКонтакте, "
    "Telegram, Google, Яндекс и любые другие внешние сервисы или соцсети. "
    "Никаких сравнений с внешними платформами и никаких рекомендаций по ним.\n"
    "- НИКОГДА не делай выводов о динамике, трендах и сравнении периодов, "
    "если в данных нет явного столбца с датой или периодом. "
    "Если такого столбца нет — анализируй данные как единый срез без временной динамики."
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
    return """Составь клиентский QBR-отчёт. Тон — позитивный, профессиональный, партнёрский.

ВАЖНЫЕ ПРАВИЛА:
- НЕ упоминай низкие показатели, отклонения от нормы, проблемы, аутсайдеров, СРОЧНО
- НЕ используй ⚠️ 🔴 и любые сигналы тревоги
- Показывай только сильные стороны, достижения и возможности роста
- Сравнивай Video только с Video, Display только с Display — никогда между форматами

## 1. Executive Summary
3–4 предложения: главный позитивный итог периода + 3 ключевые цифры-достижения.

## 2. Распределение бюджета
- Общий бюджет и разбивка по рекламодателям (% от общего)
- Распределение бюджета между форматами Video и Display (% и суммы)
- Если есть динамика по периодам — показать рост бюджета по месяцам/кварталам ✅

## 3. Динамика показателей (ТОЛЬКО если в данных есть столбец с датой или периодом)
Если столбца с датой нет — этот раздел полностью пропусти, не упоминай его.
Если даты есть: тренд по периодам бюджет/показы/клики, выделить лучшие периоды.

## 4. Топ кампаний — Video
✅ ТОП-3 кампании по VTR с цифрами. Что сработало хорошо.

## 5. Топ кампаний — Display
✅ ТОП-3 кампании по CTR с цифрами. Что сработало хорошо.

## 6. Зелёные зоны эффективности
Только лучшие показатели: где CTR высокий, где VTR высокий, где CPM оптимальный.
Формат: ✅ [Рекламодатель / Кампания] — [метрика] [значение] — [почему это хорошо]

## 7. Возможности для развития
2–3 направления для масштабирования успешных результатов.
Формат: **[Направление]** → что уже работает → как усилить в следующем периоде

Пиши на русском. Только цифры и факты. Никакого негатива."""

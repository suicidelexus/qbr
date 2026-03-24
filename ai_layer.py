"""
AI Layer — генерация инсайтов через Groq LLM
"""
import pandas as pd
from typing import Dict, List
from processing_layer import AnalysisEngine
import config


# ════════════════════════════════════════════════════════
#  LLM-powered Insight Generator (Groq)
# ════════════════════════════════════════════════════════

class LLMInsightGenerator:
    """
    Генерация инсайтов через Groq LLM (бесплатно!)
    Получить ключ: https://console.groq.com/keys
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or config.GROQ_API_KEY
        self.model = model or config.GROQ_MODEL
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    def _chat(self, system: str, user: str, max_tokens: int = 2000) -> str:
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content

    @staticmethod
    def _df_summary(df: pd.DataFrame, max_rows: int = 30) -> str:
        """Компактная сводка DataFrame для промпта"""
        if df.empty:
            return "(пустой DataFrame)"
        parts = [
            f"Колонки: {list(df.columns)}",
            f"Строк: {len(df)}",
            f"--- describe ---\n{df.describe(include='all').to_string()}",
        ]
        if len(df) <= max_rows:
            parts.append(f"--- data ---\n{df.to_string(index=False)}")
        else:
            parts.append(f"--- top 15 ---\n{df.head(15).to_string(index=False)}")
            parts.append(f"--- bottom 5 ---\n{df.tail(5).to_string(index=False)}")
        return "\n".join(parts)

    SYSTEM_PROMPT = (
        "Ты — senior media-аналитик DSP-платформы Hybrid.ai. "
        "Твоя задача — НЕ описывать данные, а находить инсайты, "
        "объяснять причины и давать конкретные рекомендации по оптимизации бюджета. "
        "Пиши на русском. Формат: markdown. Будь конкретен, указывай цифры."
    )

    def analyze_advertisers(self, df: pd.DataFrame) -> str:
        return self._chat(
            self.SYSTEM_PROMPT,
            f"Данные по рекламодателям (TotalSum по месяцам):\n{self._df_summary(df)}\n\n"
            "Найди инсайты по расходам: тренды, аномалии, рекомендации по бюджету.",
        )

    def analyze_dynamics(self, df: pd.DataFrame) -> str:
        return self._chat(
            self.SYSTEM_PROMPT,
            f"Динамика метрик (месяц × рекламодатель × BannerType), без TotalSum:\n{self._df_summary(df)}\n\n"
            "Найди ключевые тренды, проблемные зоны, возможности для оптимизации.",
        )

    def analyze_banner_sizes(self, df: pd.DataFrame) -> str:
        return self._chat(
            self.SYSTEM_PROMPT,
            f"Данные по BannerSize (display):\n{self._df_summary(df)}\n\n"
            "Какие размеры наиболее/наименее эффективны? Рекомендации по оптимизации размеров.",
        )

    def generate_competitive_summary(self, all_data: Dict[str, pd.DataFrame]) -> str:
        parts = []
        for name, df in all_data.items():
            if not df.empty:
                parts.append(f"=== {name} ===\n{self._df_summary(df)}")
        return self._chat(
            self.SYSTEM_PROMPT + " Это конкурентный анализ нескольких рекламодателей.",
            "\n\n".join(parts) + "\n\nСравни рекламодателей. Кто лидер? Где возможности? Рекомендации.",
            max_tokens=3000,
        )

    def generate_qbr(self, all_data: Dict[str, pd.DataFrame]) -> str:
        parts = []
        for name, df in all_data.items():
            if not df.empty:
                parts.append(f"=== {name} ===\n{self._df_summary(df)}")
        return self._chat(
            self.SYSTEM_PROMPT + (
                " Составь Quarterly Business Review (QBR). "
                "Структура: Executive Summary, Ключевые метрики, Тренды, "
                "Проблемные зоны, Возможности, Рекомендации, Следующие шаги."
            ),
            "\n\n".join(parts),
            max_tokens=4000,
        )


# ════════════════════════════════════════════════════════
#  Rule-based fallback (без LLM)
# ════════════════════════════════════════════════════════

class InsightGenerator:
    """Rule-based генератор инсайтов (fallback без LLM)"""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.engine = AnalysisEngine(df)
        self.insights = []
        self.recommendations = []
        self.hypotheses = []

    def generate_full_analysis(self) -> Dict:
        advertisers = self.engine.compare_advertisers()
        advertiser_insights = self._analyze_advertisers(advertisers)

        products = self.engine.compare_products()
        product_insights = self._analyze_products(products)

        bt_col = 'banner_type' if 'banner_type' in self.df.columns else (
            'format' if 'format' in self.df.columns else None)
        media_split = self.engine.media_split(bt_col) if bt_col else pd.DataFrame()
        media_insights = self._analyze_media_split(media_split)

        dynamics = self.engine.dynamics('M')
        dynamics_insights = self._analyze_dynamics(dynamics)

        budget_opt = self.engine.budget_optimization()
        budget_insights = self._analyze_budget_optimization(budget_opt)

        return {
            'tldr': self._generate_tldr(),
            'advertisers': {'data': advertisers, 'insights': advertiser_insights},
            'products': {'data': products, 'insights': product_insights},
            'media_split': {'data': media_split, 'insights': media_insights},
            'dynamics': {'data': dynamics, 'insights': dynamics_insights},
            'budget_optimization': {'data': budget_opt, 'insights': budget_insights},
            'recommendations': self.recommendations,
            'hypotheses': self.hypotheses,
        }

    # ── helpers ──

    def _resolve_adv_col(self, df: pd.DataFrame) -> str:
        for col in ('advertiser', 'advertiser_id', 'advertiser_source'):
            if col in df.columns:
                return col
        return 'advertiser'

    def _analyze_advertisers(self, df: pd.DataFrame) -> List[str]:
        insights = []
        if df.empty:
            return insights
        adv_col = self._resolve_adv_col(df)
        if 'ctr' in df.columns:
            top = df.nlargest(1, 'ctr').iloc[0]
            insights.append(f"Лидер по CTR: {top[adv_col]} ({top['ctr']:.3%})")
            avg = df['ctr'].mean()
            if avg < config.CTR_BENCHMARK:
                insights.append(f"[!] Средний CTR ({avg:.3%}) ниже бенчмарка")
                self.recommendations.append("Пересмотреть креативы и таргетинг")
        if 'TotalSum' in df.columns:
            top_s = df.nlargest(1, 'TotalSum').iloc[0]
            total = df['TotalSum'].sum()
            share = top_s['TotalSum'] / total if total > 0 else 0
            insights.append(f"Крупнейший: {top_s[adv_col]} ({share:.1%} бюджета)")
        return insights

    def _analyze_products(self, df: pd.DataFrame) -> List[str]:
        if df.empty or 'product' not in df.columns:
            return []
        insights = []
        if 'ctr' in df.columns:
            top = df.nlargest(1, 'ctr').iloc[0]
            insights.append(f"Лучший продукт: {top.get('product', '?')} (CTR {top['ctr']:.3%})")
        return insights

    def _analyze_media_split(self, df: pd.DataFrame) -> List[str]:
        if df.empty:
            return []
        insights = []
        if 'spend_share' in df.columns:
            top = df.nlargest(1, 'spend_share').iloc[0]
            insights.append(f"Основной формат: {top.iloc[0]} ({top['spend_share']:.1%} бюджета)")
        return insights

    def _analyze_dynamics(self, df: pd.DataFrame) -> List[str]:
        if df.empty or len(df) < 2:
            return []
        insights = []
        if 'ctr' in df.columns:
            first, last = df.iloc[0]['ctr'], df.iloc[-1]['ctr']
            chg = (last - first) / first if first > 0 else 0
            trend = "↑ рост" if chg > .05 else "↓ снижение" if chg < -.05 else "→ стабильность"
            insights.append(f"CTR: {trend} ({chg:+.1%})")
        if 'TotalSum' in df.columns:
            first, last = df.iloc[0]['TotalSum'], df.iloc[-1]['TotalSum']
            chg = (last - first) / first if first > 0 else 0
            insights.append(f"Бюджет: {chg:+.1%}")
        return insights

    def _analyze_budget_optimization(self, data: Dict) -> List[str]:
        if not data:
            return []
        insights = [f"Бюджет: {data.get('total_spend', 0):,.0f}, CTR: {data.get('avg_ctr', 0):.3%}"]
        for adv in data.get('underperformers', [])[:3]:
            self.recommendations.append(f"Сократить бюджет: {adv['advertiser']} (CTR {adv['ctr']:.3%})")
        for adv in data.get('overperformers', [])[:3]:
            self.recommendations.append(f"Увеличить бюджет: {adv['advertiser']} (CTR {adv['ctr']:.3%})")
        return insights

    def _generate_tldr(self) -> str:
        spend = self.df['TotalSum'].sum() if 'TotalSum' in self.df.columns else 0
        imps = self.df['impressions'].sum() if 'impressions' in self.df.columns else 0
        ctr = self.df['ctr'].mean() if 'ctr' in self.df.columns else 0
        return f"Бюджет: {spend:,.0f} | Показы: {imps:,.0f} | CTR: {ctr:.3%}"

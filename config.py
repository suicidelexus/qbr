"""
Configuration — constants only
"""

# ── Colors ────────────────────────────────────────────────
BRAND_COLORS = ["#4F46E5", "#7C3AED", "#2563EB", "#059669", "#D97706", "#DC2626", "#0891B2", "#BE185D"]

COLOR = {
    "primary":   "#4F46E5",
    "secondary": "#7C3AED",
    "success":   "#059669",
    "warning":   "#D97706",
    "danger":    "#DC2626",
    "info":      "#0891B2",
    "text":      "#1F2937",
    "muted":     "#6B7280",
    "bg":        "#F9FAFB",
}

PLOTLY_TEMPLATE = "plotly_white"

# ── Benchmarks ────────────────────────────────────────────
CTR_BENCHMARK        = 0.001   # 0.1% — Display
CTR_BENCHMARK_VIDEO  = 0.004   # 0.4% — Video
CTR_ANOMALY_HIGH_DISPLAY = 0.004   # > 0.4% anomaly for Display
CTR_ANOMALY_HIGH_VIDEO   = 0.015   # > 1.5% anomaly for Video
VIEWABILITY_BENCHMARK = 0.70   # 70%
VTR_BENCHMARK        = 0.25    # 25%
MIN_IMPRESSIONS      = 1000

# ── LLM providers ─────────────────────────────────────────
LLM_PROVIDERS = {
    "Mistral AI":     {"base_url": "https://api.mistral.ai/v1", "default_model": "mistral-small-latest"},
    "Custom (proxy)": {"base_url": "", "default_model": ""},
}

# ── Standard column mapping ───────────────────────────────
STANDARD_COLS = {
    "date":       ["date", "дата", "день", "day", "month", "период", "месяц", "неделя", "week"],
    "advertiser": ["advertiser", "рекламодатель", "клиент", "client", "бренд", "brand",
                   "advertiser_id", "advertiser_source"],
    "campaign":   ["campaign", "кампания", "кампании", "camp", "campaign_name", "название кампании"],
    "format":     ["format", "формат", "формат креатива", "тип креатива", "banner_type",
                   "тип", "type", "вид", "канал"],
    "banner_size":["banner_size", "size", "размер", "creative_size", "banner size",
                   "размер баннера", "размер креатива"],
    "product":    ["product", "продукт", "товар", "категория продукта"],
    "impressions":["impressions", "imp", "показы", "импрессии", "views", "показ"],
    "clicks":     ["clicks", "click", "клики", "кликов", "кликов за период"],
    "TotalSum":   ["totalsum", "total_sum", "бюджет", "budget", "расход", "spend", "затраты",
                   "cost", "total", "сумма", "общий расход", "расходы", "потрачено", "списано"],
    "ctr":        ["ctr", "click-through rate", "кликабельность"],
    "cpm":        ["cpm", "cost per mille", "цена за тысячу"],
    "cpc":        ["cpc", "cost per click", "цена за клик"],
    "viewability":["viewability", "видимость", "viewable"],
    "vtr":        ["vtr", "view_rate", "view through rate", "досматриваемость"],
    "frequency":  ["frequency", "частота", "freq", "средняя частота"],
    "reach":      ["reach", "охват", "unique reach"],
}

BENCHMARKS = {
    "ctr":        CTR_BENCHMARK,
    "viewability": VIEWABILITY_BENCHMARK,
    "vtr":        VTR_BENCHMARK,
}

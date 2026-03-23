"""
Конфигурация DSP Analytics Platform
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
# Hybrid.ai DSP Platform (https://docs.hybrid.ai/rest-api-3-0)
# Credentials можно задать через .env или ввести в Dashboard UI
DSP_CLIENT_ID = os.getenv('DSP_CLIENT_ID')    # Обязательно!
DSP_SECRET_KEY = os.getenv('DSP_SECRET_KEY')  # Обязательно!

# LLM Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

# Metrics Configuration
CORE_METRICS = [
    'impressions',
    'clicks',
    'ctr',
    'cpc',
    'cpm',
    'viewability',
    'vtr',
    'frequency',
    'TotalSum'
]

CONVERSION_METRICS = [
    'post_click_conversions',
    'post_view_conversions',
    'conversion_value',
    'revenue'
]

ALL_METRICS = CORE_METRICS + CONVERSION_METRICS

# Dimensions
DIMENSIONS = [
    'date',
    'advertiser',
    'category',
    'product',
    'campaign',
    'format',
    'banner_type',
    'banner_size',
    'creative_size',
    'audience_segment'
]

# BannerSize groups
BANNER_SIZE_PRIMARY = ['300x250', '300x600', '336x280', '240x400', '320x480']
BANNER_SIZE_SECONDARY = ['320x100', '320x50', '640x360', '300x50', '300x300', '728x90', '160x600']
BANNER_SIZE_ALL = BANNER_SIZE_PRIMARY + BANNER_SIZE_SECONDARY

# Analysis Thresholds
MIN_IMPRESSIONS = 1000  # Минимум для статистической значимости
CTR_BENCHMARK = 0.001   # 0.1%
VTR_BENCHMARK = 0.25    # 25%
VIEWABILITY_BENCHMARK = 0.70  # 70%

# Visualization
CHART_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

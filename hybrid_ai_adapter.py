"""
Hybrid.ai DSP API Adapter
Обёртка над DSPClient с Hybrid-специфичными методами
Документация: https://docs.hybrid.ai/rest-api-3-0
"""
from data_layer import DSPClient
import pandas as pd
from typing import List, Dict, Optional


class HybridAIClient(DSPClient):
    """
    Расширенный клиент для Hybrid.ai DSP API

    Наследует DSPClient (OAuth2 Bearer auth).
    Добавляет удобные методы для типичных задач.
    """

    def __init__(self, client_id: str = None, secret_key: str = None, **kwargs):
        kwargs.pop('api_url', None)  # не нужен, URL зафиксирован
        super().__init__(client_id=client_id, secret_key=secret_key, **kwargs)

    def get_agency_stats_by_day(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Статистика по агентству с группировкой по дням"""
        return self.get_report(start_date=start_date, end_date=end_date, split='Day')

    def get_agency_stats_by_advertiser(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Статистика по агентству с группировкой по рекламодателям"""
        return self.get_report(start_date=start_date, end_date=end_date, split='Advertiser')

    def get_advertiser_stats(
        self, advertiser_id: str, start_date: str, end_date: str,
        split: str = 'Day'
    ) -> pd.DataFrame:
        """Статистика по конкретному рекламодателю"""
        return self.get_report(
            start_date=start_date, end_date=end_date,
            split=split, level='advertiser', entity_id=advertiser_id
        )

    def get_campaign_stats(
        self, campaign_id: str, start_date: str, end_date: str,
        split: str = 'Day'
    ) -> pd.DataFrame:
        """Статистика по конкретной кампании"""
        return self.get_report(
            start_date=start_date, end_date=end_date,
            split=split, level='campaign', entity_id=campaign_id
        )

    def get_campaigns_list(self, advertiser_id: str = None, **kwargs) -> pd.DataFrame:
        """Алиас для get_campaigns"""
        return self.get_campaigns(advertiser_id=advertiser_id)

    def get_creatives(self, campaign_id: str = None, **kwargs) -> pd.DataFrame:
        """Алиас для get_banners"""
        return self.get_banners(campaign_id=campaign_id)


def create_hybrid_client(**kwargs) -> HybridAIClient:
    return HybridAIClient(**kwargs)

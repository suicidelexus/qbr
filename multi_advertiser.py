"""
Multi-Advertiser Manager
Загрузка и сравнение данных из нескольких API credentials
"""
import pandas as pd
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from data_layer import DSPClient
from processing_layer import DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiAdvertiserManager:
    """
    Менеджер для работы с несколькими рекламодателями из разных API credentials.

    Каждый credential (client_id + secret_key) может быть agency-токеном
    с N рекламодателями внутри. Менеджер загружает все 3 сплита
    (Day, BannerType, BannerSize) для каждого и объединяет.
    """

    def __init__(self, credentials: List[Dict] = None):
        self.credentials = credentials or []
        self.clients: Dict[str, DSPClient] = {}
        self.processor = DataProcessor()

        if self.credentials:
            self._initialize_clients()

    def _initialize_clients(self):
        for cred in self.credentials:
            label = cred.get('advertiser', cred.get('label', ''))
            cid = cred.get('client_id')
            skey = cred.get('secret_key')
            if not cid or not skey:
                continue
            try:
                client = DSPClient(client_id=cid, secret_key=skey)
                self.clients[label] = client
                logger.info(f"✓ Клиент создан: {label}")
            except Exception as e:
                logger.error(f"✗ {label}: {e}")

    def add_credential(self, label: str, client_id: str, secret_key: str) -> bool:
        try:
            client = DSPClient(client_id=client_id, secret_key=secret_key)
            self.clients[label] = client
            self.credentials.append({
                'advertiser': label, 'client_id': client_id, 'secret_key': secret_key,
            })
            return True
        except Exception as e:
            logger.error(f"✗ {label}: {e}")
            return False

    # ── Загрузка всех сплитов ──

    def load_all_splits(
        self,
        start_date: str,
        end_date: str,
        progress_callback=None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Загрузка Day / BannerType / BannerSize для каждого credential.

        Returns: {'day': df, 'banner_type': df, 'banner_size': df}
        """
        day_frames, bt_frames, bs_frames = [], [], []

        total = len(self.clients)
        for idx, (label, client) in enumerate(self.clients.items()):
            if progress_callback:
                progress_callback(idx, total, label)
            logger.info(f"[MULTI] Загрузка {label} ({idx+1}/{total})...")

            try:
                splits = client.get_all_splits_data(
                    start_date=start_date,
                    end_date=end_date,
                )
                for key, frames in [('day', day_frames), ('banner_type', bt_frames), ('banner_size', bs_frames)]:
                    df = splits.get(key, pd.DataFrame())
                    if not df.empty:
                        df['credential_source'] = label
                        frames.append(df)

                logger.info(f"  ✓ {label}: day={len(splits.get('day', []))} "
                            f"bt={len(splits.get('banner_type', []))} "
                            f"bs={len(splits.get('banner_size', []))}")
            except Exception as e:
                logger.error(f"  ✗ {label}: {e}")

        def _concat(frames):
            if not frames:
                return pd.DataFrame()
            combined = pd.concat(frames, ignore_index=True)
            return self.processor.calculate_derived_metrics(combined)

        return {
            'day': _concat(day_frames),
            'banner_type': _concat(bt_frames),
            'banner_size': _concat(bs_frames),
        }

    # ── Утилиты для сравнения ──

    def get_comparison_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        adv_col = None
        for c in ('advertiser', 'advertiser_source', 'credential_source'):
            if c in df.columns:
                adv_col = c
                break
        if not adv_col or df.empty:
            return pd.DataFrame()
        summary = self.processor.aggregate_by(df, group_by=[adv_col])
        if 'ctr' in summary.columns:
            summary = summary.sort_values('ctr', ascending=False)
        return summary

    def compare_by_dimension(self, df: pd.DataFrame, dimension: str) -> pd.DataFrame:
        adv_col = None
        for c in ('advertiser', 'advertiser_source', 'credential_source'):
            if c in df.columns:
                adv_col = c
                break
        if not adv_col or dimension not in df.columns:
            return pd.DataFrame()
        return self.processor.aggregate_by(df, group_by=[adv_col, dimension])

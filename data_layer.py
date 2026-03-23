"""
Data Layer - работа с Hybrid.ai DSP REST API v3.0
Документация: https://docs.hybrid.ai/rest-api-3-0

Аутентификация: OAuth2 Client Credentials
  POST https://api.hybrid.ai/token
  Content-Type: application/x-www-form-urlencoded

Два типа токенов:
  - agency    → GET /v3.0/agency/...     (доступ ко всем рекламодателям)
  - advertiser → GET /v3.0/advertiser/... (advertiserId из токена, split необязателен)

Endpoints:
  GET /v3.0/agency/advertisers                         — список рекламодателей (agency)
  GET /v3.0/advertiser/campaigns?advertiserId={id}     — список кампаний
  GET /v3.0/campaign/banners?campaignId={id}           — список баннеров
  GET /v3.0/agency/{split}?from=...&to=...             — статистика (agency)
  GET /v3.0/advertiser/{split}?from=...&to=...         — статистика (advertiser)
  GET /v3.0/campaign/{split}?from=...&to=...&campaignId={id} — статистика (campaign)

Splits: Day, Advertiser, Country, Region, Ssp, Folder
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import config
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Hybrid.ai API URLs (из официальной документации)
TOKEN_URL = 'https://api.hybrid.ai/token'
API_BASE = 'https://api.hybrid.ai/v3.0'

# Маппинг полей API → стандартный формат проекта
FIELD_MAPPING = {
    'Day': 'date',
    'ImpressionCount': 'impressions',
    'ViewCount': 'views',
    'ClickCount': 'clicks',
    'CTR': 'ctr',
    'Viewability': 'viewability',
    'Frequency': 'frequency',
    'Reach': 'reach',
    'PostClickConversionsCount': 'post_click_conversions',
    'PostViewConversionsCount': 'post_view_conversions',
    'FirstQuartileEventsCount': 'vtr_25',
    'MidpointEventsCount': 'vtr_50',
    'ThirdQuartileEventsCount': 'vtr_75',
    'CompleteEventsCount': 'vtr_100',
    'Advertiser': 'advertiser_id',
    'BannerType': 'banner_type',
    'BannerSize': 'banner_size',
    'Country': 'country',
    'Region': 'region',
    'Ssp': 'ssp',
    'Folder': 'folder',
}


class DSPClient:
    """
    Клиент для Hybrid.ai DSP REST API v3.0
    Автоматически определяет тип токена (agency / advertiser).
    """

    def __init__(
        self,
        client_id: str = None,
        secret_key: str = None,
        timeout: int = 60,
        max_retries: int = 3,
        rate_limit_delay: float = 0.1
    ):
        self.client_id = client_id or config.DSP_CLIENT_ID
        self.secret_key = secret_key or getattr(config, 'DSP_SECRET_KEY', None)
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay

        if not self.client_id or not self.secret_key:
            raise ValueError("Client ID и Secret Key обязательны для работы с Hybrid.ai API")

        self.session = self._create_session(max_retries)

        # OAuth2 state
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._token_type: Optional[str] = None  # 'agency' или 'advertiser'

    def _create_session(self, max_retries: int) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    # ==================== AUTH ====================

    def _authenticate(self):
        """
        OAuth2 Client Credentials → access_token
        POST https://api.hybrid.ai/token
        """
        try:
            resp = self.session.post(
                TOKEN_URL,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.secret_key,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            body = e.response.text[:500]
            raise RuntimeError(
                f"Ошибка аутентификации HTTP {status}\n"
                f"URL: {TOKEN_URL}\nОтвет: {body}\n\n"
                f"Проверьте Client ID и Secret Key"
            )
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Нет соединения с сервером\nURL: {TOKEN_URL}")
        except Exception as e:
            raise RuntimeError(f"Ошибка аутентификации: {e}")

        self._access_token = data.get('access_token')
        self._refresh_token = data.get('refresh_token')
        if not self._access_token:
            raise RuntimeError(f"access_token не получен. Ответ: {data}")

        expires_in = data.get('expires_in', 86399)
        self._token_expires_at = time.time() + expires_in - 120
        print(f"[AUTH] Токен получен, expires_in={expires_in}s")

    def _detect_token_type(self):
        """
        Определяет тип токена: agency или advertiser.
        Пробует agency endpoint — если 400, значит advertiser.
        """
        if self._token_type:
            return

        self._ensure_token()
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Accept': 'application/json'
        }

        try:
            resp = self.session.get(
                f"{API_BASE}/agency/advertisers",
                headers=headers,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                self._token_type = 'agency'
                print(f"[AUTH] Тип токена: agency")
                return
        except Exception:
            pass

        self._token_type = 'advertiser'
        print(f"[AUTH] Тип токена: advertiser")

    @property
    def token_type(self) -> str:
        """Тип токена: 'agency' или 'advertiser'"""
        if not self._token_type:
            self._detect_token_type()
        return self._token_type

    def _ensure_token(self):
        if not self._access_token or time.time() >= self._token_expires_at:
            self._access_token = None
            self._token_type = None  # сброс при новом токене
            self._authenticate()

    def _auth_headers(self) -> Dict[str, str]:
        self._ensure_token()
        return {
            'Authorization': f'Bearer {self._access_token}',
            'Accept': 'application/json'
        }

    # ==================== HTTP ====================

    def _get(self, endpoint: str, params: Dict = None) -> Any:
        """GET запрос к API"""
        url = f"{API_BASE}/{endpoint.lstrip('/')}"
        time.sleep(self.rate_limit_delay)
        headers = self._auth_headers()
        print(f"[API] GET {url}  params={params}")

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)

            if response.status_code == 401:
                self._access_token = None
                self._token_type = None
                headers = self._auth_headers()
                response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            print(f"HTTP {e.response.status_code}: {e.response.text[:300]}")
            raise
        except requests.exceptions.ConnectionError as e:
            print(f"Ошибка соединения: {e}")
            raise

    # ==================== ADVERTISERS ====================

    def get_advertisers(self) -> pd.DataFrame:
        """
        GET /v3.0/agency/advertisers (только для agency-токена)
        Для advertiser-токена возвращает пустой DataFrame.

        Ответ API: [{"Id": "...", "Name": "advertiser1"}, ...]
        Нормализуем: Id → advertiser_id, Name → advertiser
        """
        if self.token_type != 'agency':
            print("get_advertisers доступен только для agency-токена")
            return pd.DataFrame()

        try:
            data = self._get('agency/advertisers')
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data.get('data', data.get('Advertisers', [])))

            if not df.empty:
                rename = {}
                if 'Id' in df.columns:
                    rename['Id'] = 'advertiser_id'
                if 'Name' in df.columns:
                    rename['Name'] = 'advertiser'
                if rename:
                    df = df.rename(columns=rename)

            return df
        except Exception as e:
            print(f"Ошибка получения рекламодателей: {e}")
            return pd.DataFrame()

    def _get_advertiser_map(self) -> Dict[str, str]:
        """
        Возвращает маппинг {advertiser_id: advertiser_name}.
        Кэширует результат на время жизни клиента.
        """
        if not hasattr(self, '_adv_map_cache'):
            advs = self.get_advertisers()
            if (not advs.empty
                    and 'advertiser_id' in advs.columns
                    and 'advertiser' in advs.columns):
                self._adv_map_cache = dict(
                    zip(advs['advertiser_id'].astype(str), advs['advertiser'])
                )
            else:
                self._adv_map_cache = {}
        return self._adv_map_cache

    # ==================== CAMPAIGNS ====================

    def get_campaigns(self, advertiser_id: str = None, **kwargs) -> pd.DataFrame:
        """GET /v3.0/advertiser/campaigns"""
        params = {}
        if advertiser_id:
            params['advertiserId'] = advertiser_id

        try:
            data = self._get('advertiser/campaigns', params=params)
            if isinstance(data, list):
                return pd.DataFrame(data)
            return pd.DataFrame(data.get('data', []))
        except Exception as e:
            print(f"Ошибка получения кампаний: {e}")
            return pd.DataFrame()

    # ==================== BANNERS ====================

    def get_banners(self, campaign_id: str = None) -> pd.DataFrame:
        """GET /v3.0/campaign/banners?campaignId={campaignId}"""
        params = {}
        if campaign_id:
            params['campaignId'] = campaign_id

        try:
            data = self._get('campaign/banners', params=params)
            if isinstance(data, list):
                return pd.DataFrame(data)
            return pd.DataFrame(data.get('data', []))
        except Exception as e:
            print(f"Ошибка получения баннеров: {e}")
            return pd.DataFrame()

    # ==================== STATISTICS ====================

    def get_statistics(
        self,
        start_date: str,
        end_date: str,
        split: str = 'Day',
        split2: str = None,
        level: str = None,
        entity_id: str = None,
        page: int = 0,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Получение статистики.

        level: 'agency', 'advertiser', 'campaign'.
               Если None — определяется автоматически по типу токена.
        entity_id: advertiserId / campaignId (для agency-токена обязателен
                   при level=advertiser; для advertiser-токена — не нужен).
        """
        if level is None:
            level = self.token_type  # agency или advertiser

        path = f"{level}/{split}"
        if split2:
            path = f"{level}/{split}/{split2}"

        params = {
            'from': start_date,
            'to': end_date,
            'page': page,
            'limit': limit,
        }

        if level == 'advertiser' and entity_id:
            params['advertiserId'] = entity_id
        elif level == 'campaign' and entity_id:
            params['campaignId'] = entity_id

        try:
            data = self._get(path, params=params)
        except Exception as e:
            print(f"[STAT] Ошибка {level}/{split}: {e}")
            return pd.DataFrame()

        return self._parse_statistics_response(data)

    def get_statistics_all_pages(
        self,
        start_date: str,
        end_date: str,
        split: str = 'Day',
        split2: str = None,
        level: str = None,
        entity_id: str = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Загрузка статистики со всех страниц"""
        all_rows = []
        page = 0

        while True:
            print(f"[STAT] Загрузка {level or self.token_type}/{split}"
                  f"{('/' + split2) if split2 else ''}"
                  f"  стр. {page}  ({start_date} — {end_date})")
            df = self.get_statistics(
                start_date=start_date, end_date=end_date,
                split=split, split2=split2,
                level=level, entity_id=entity_id,
                page=page, limit=limit,
            )

            if df.empty:
                break

            all_rows.append(df)
            if len(df) < limit:
                break

            page += 1

        if not all_rows:
            return pd.DataFrame()

        result = pd.concat(all_rows, ignore_index=True)
        print(f"Загружено {len(result)} строк ({page + 1} стр.)")
        return result

    def _parse_statistics_response(self, data: Any) -> pd.DataFrame:
        if isinstance(data, dict):
            rows = data.get('Statistic', data.get('statistic', data.get('data', [])))
            if not rows:
                print(f"[STAT] Ответ API (dict keys): {list(data.keys())}")
        elif isinstance(data, list):
            rows = data
        else:
            print(f"[STAT] Неожиданный тип ответа: {type(data)}")
            return pd.DataFrame()

        if not rows:
            print("[STAT] Пустой ответ — 0 строк")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        print(f"[STAT] Получено {len(df)} строк, колонки: {list(df.columns)}")
        return self._normalize_fields(df)

    def _normalize_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        df = df.copy()
        rename_map = {k: v for k, v in FIELD_MAPPING.items() if k in df.columns}
        df = df.rename(columns=rename_map)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        if 'ctr' in df.columns:
            max_ctr = df['ctr'].max()
            if max_ctr > 1:
                df['ctr'] = df['ctr'] / 100.0

        numeric = [c for c in df.columns if c in config.ALL_METRICS]
        for col in numeric:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Резолвим advertiser_id → advertiser (имя) через кэш
        if 'advertiser_id' in df.columns and 'advertiser' not in df.columns:
            try:
                adv_map = self._get_advertiser_map()
                if adv_map:
                    df['advertiser'] = (
                        df['advertiser_id']
                        .astype(str)
                        .map(adv_map)
                        .fillna(df['advertiser_id'])
                    )
                else:
                    # Нет маппинга (advertiser-токен) — используем ID как имя
                    df['advertiser'] = df['advertiser_id']
            except Exception:
                df['advertiser'] = df['advertiser_id']

        return df

    # ==================== PER-ADVERTISER LOADING ====================

    def get_stats_per_advertiser(
        self,
        split: str,
        start_date: str,
        end_date: str,
        progress_callback=None,
    ) -> pd.DataFrame:
        """
        Загрузка статистики для КАЖДОГО рекламодателя отдельно.

        Flow (agency-токен):
          1. GET /agency/advertisers → [{Id, Name}, ...]
          2. Для каждого Id:
             GET /advertiser/{split}?advertiserId={Id}&from=...&to=...
          3. Добавляем колонку advertiser = Name
          4. Конкатенируем

        Для advertiser-токена: один вызов без advertiserId.
        """
        if self.token_type != 'agency':
            # Для advertiser-токена — один вызов
            df = self.get_statistics_all_pages(
                start_date=start_date, end_date=end_date,
                split=split, level='advertiser',
            )
            if not df.empty and 'advertiser' not in df.columns:
                df['advertiser'] = 'My Advertiser'
            return df

        # --- Agency: загружаем список рекламодателей ---
        advertisers_df = self.get_advertisers()
        if advertisers_df.empty:
            print("[LOAD] Нет рекламодателей")
            return pd.DataFrame()

        adv_list = list(zip(
            advertisers_df['advertiser_id'].astype(str),
            advertisers_df['advertiser'],
        ))
        print(f"[LOAD] {len(adv_list)} рекламодателей, split={split}")

        frames = []
        for idx, (adv_id, adv_name) in enumerate(adv_list):
            if progress_callback:
                progress_callback(idx, len(adv_list), adv_name, split)

            print(f"[LOAD]   {idx+1}/{len(adv_list)} {adv_name} ({split})...")
            df = self.get_statistics_all_pages(
                start_date=start_date, end_date=end_date,
                split=split,
                level='advertiser',
                entity_id=adv_id,
            )
            if not df.empty:
                df['advertiser'] = adv_name
                df['advertiser_id'] = adv_id
                frames.append(df)
                print(f"[LOAD]     → {len(df)} строк")
            else:
                print(f"[LOAD]     → пусто")

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames, ignore_index=True)
        print(f"[LOAD] Итого split={split}: {len(result)} строк от {len(frames)} рекламодателей")
        return result

    def get_all_splits_data(
        self,
        start_date: str,
        end_date: str,
        progress_callback=None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Загрузка всех нужных split-ов для dashboard.

        Returns: {
            'day':         DataFrame (split=Day, per advertiser),
            'banner_type': DataFrame (split=BannerType, per advertiser),
            'banner_size': DataFrame (split=BannerSize, per advertiser),
        }
        """
        return {
            'day': self.get_stats_per_advertiser(
                'Day', start_date, end_date, progress_callback,
            ),
            'banner_type': self.get_stats_per_advertiser(
                'BannerType', start_date, end_date, progress_callback,
            ),
            'banner_size': self.get_stats_per_advertiser(
                'BannerSize', start_date, end_date, progress_callback,
            ),
        }

    # ==================== CONVENIENCE ====================

    def get_report(
        self,
        start_date: str,
        end_date: str,
        split: str = 'Day',
        split2: str = None,
        level: str = None,
        entity_id: str = None,
        **kwargs
    ) -> pd.DataFrame:
        return self.get_statistics_all_pages(
            start_date=start_date, end_date=end_date,
            split=split, split2=split2,
            level=level, entity_id=entity_id,
        )

    get_data = get_report

    def get_last_n_days(self, days: int = 30, **kwargs) -> pd.DataFrame:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return self.get_report(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            **kwargs
        )

    def test_connection(self) -> bool:
        """
        Тест подключения:
          1. Получаем токен
          2. Определяем тип (agency / advertiser)
          3. Проверяем доступ к данным
        """
        # 1. Токен
        try:
            self._authenticate()
        except RuntimeError:
            raise

        # 2. Определяем тип и проверяем доступ
        self._detect_token_type()

        if self._token_type == 'agency':
            info = "agency (доступ ко всем рекламодателям)"
        else:
            # Проверяем что advertiser endpoint работает
            try:
                self._get('advertiser/campaigns')
                info = "advertiser (один рекламодатель)"
            except Exception as e:
                raise RuntimeError(
                    f"Токен получен ✓, тип: advertiser, но ошибка запроса: {e}"
                )

        print(f"[OK] Подключение успешно, тип токена: {self._token_type}")
        return True


class DataLoader:
    """Загрузка данных из разных источников"""

    def _create_api_client(self, client_id: str = None, secret_key: str = None) -> DSPClient:
        return DSPClient(client_id=client_id, secret_key=secret_key)

    def load_from_api(self, client_id: str = None, secret_key: str = None, **kwargs) -> pd.DataFrame:
        client = self._create_api_client(client_id=client_id, secret_key=secret_key)
        return client.get_report(**kwargs)

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

    def load_from_excel(self, filepath: str, sheet_name: str = 0) -> pd.DataFrame:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df


"""
Google Export Module
Экспорт результатов анализа в Google Slides и Sheets
"""
import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Опциональный импорт Google API
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API библиотеки не установлены")


class GoogleSlidesExporter:
    """Экспорт в Google Slides"""
    
    def __init__(self, credentials_path: str = None):
        """
        Инициализация экспортера
        
        Args:
            credentials_path: путь к credentials.json
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Установите: pip install google-api-python-client google-auth")
        
        self.credentials_path = credentials_path or 'credentials.json'
        self.slides_service = None
        self.drive_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/presentations',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            self.slides_service = build('slides', 'v1', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("✓ Аутентификация в Google API успешна")
        except Exception as e:
            logger.error(f"✗ Ошибка аутентификации Google API: {e}")
            raise
    
    def create_presentation(
        self,
        title: str,
        analysis_results: Dict
    ) -> str:
        """
        Создание презентации с результатами анализа
        
        Args:
            title: название презентации
            analysis_results: результаты анализа
        
        Returns:
            ID созданной презентации
        """
        try:
            # Создаем презентацию
            presentation = self.slides_service.presentations().create(
                body={'title': title}
            ).execute()
            
            presentation_id = presentation['presentationId']
            logger.info(f"✓ Презентация создана: {presentation_id}")
            
            # Добавляем слайды
            self._add_title_slide(presentation_id, title, analysis_results)
            self._add_summary_slide(presentation_id, analysis_results)
            self._add_advertisers_slide(presentation_id, analysis_results)
            self._add_recommendations_slide(presentation_id, analysis_results)
            
            logger.info(f"✓ Презентация заполнена")
            
            return presentation_id
            
        except HttpError as e:
            logger.error(f"✗ Ошибка создания презентации: {e}")
            raise
    
    def _add_title_slide(self, presentation_id: str, title: str, results: Dict):
        """Добавление титульного слайда"""
        requests = [
            {
                'createSlide': {
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE'
                    }
                }
            }
        ]
        
        self.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
    
    def _add_summary_slide(self, presentation_id: str, results: Dict):
        """Добавление слайда с сводкой"""
        # TODO: Реализация добавления текста на слайд
        pass
    
    def _add_advertisers_slide(self, presentation_id: str, results: Dict):
        """Добавление слайда со сравнением advertisers"""
        # TODO: Реализация
        pass
    
    def _add_recommendations_slide(self, presentation_id: str, results: Dict):
        """Добавление слайда с рекомендациями"""
        # TODO: Реализация
        pass
    
    def get_presentation_url(self, presentation_id: str) -> str:
        """Получение URL презентации"""
        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"


class GoogleSheetsExporter:
    """Экспорт в Google Sheets"""
    
    def __init__(self, credentials_path: str = None):
        """
        Инициализация экспортера
        
        Args:
            credentials_path: путь к credentials.json
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Установите: pip install google-api-python-client google-auth")
        
        self.credentials_path = credentials_path or 'credentials.json'
        self.sheets_service = None
        self.drive_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("✓ Аутентификация в Google Sheets API успешна")
        except Exception as e:
            logger.error(f"✗ Ошибка аутентификации: {e}")
            raise
    
    def create_spreadsheet(
        self,
        title: str,
        analysis_results: Dict
    ) -> str:
        """
        Создание таблицы с результатами
        
        Args:
            title: название таблицы
            analysis_results: результаты анализа
        
        Returns:
            ID созданной таблицы
        """
        try:
            # Создаем таблицу
            spreadsheet = {
                'properties': {'title': title},
                'sheets': [
                    {'properties': {'title': 'Summary'}},
                    {'properties': {'title': 'Advertisers'}},
                    {'properties': {'title': 'Raw Data'}},
                    {'properties': {'title': 'Insights'}}
                ]
            }
            
            result = self.sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            spreadsheet_id = result['spreadsheetId']
            logger.info(f"✓ Таблица создана: {spreadsheet_id}")
            
            # Заполняем листы
            self._fill_summary_sheet(spreadsheet_id, analysis_results)
            self._fill_advertisers_sheet(spreadsheet_id, analysis_results)
            self._fill_raw_data_sheet(spreadsheet_id, analysis_results)
            self._fill_insights_sheet(spreadsheet_id, analysis_results)
            
            logger.info(f"✓ Таблица заполнена")
            
            return spreadsheet_id
            
        except HttpError as e:
            logger.error(f"✗ Ошибка создания таблицы: {e}")
            raise
    
    def _fill_summary_sheet(self, spreadsheet_id: str, results: Dict):
        """Заполнение листа Summary"""
        # TL;DR и основные метрики
        tldr = results.get('tldr', '')
        
        values = [
            ['DSP Analytics Report'],
            [''],
            ['TL;DR'],
            [tldr],
            [''],
            ['Key Metrics']
        ]
        
        self._write_values(spreadsheet_id, 'Summary!A1', values)
    
    def _fill_advertisers_sheet(self, spreadsheet_id: str, results: Dict):
        """Заполнение листа Advertisers"""
        advertisers_data = results.get('advertisers', {}).get('data', pd.DataFrame())
        
        if not advertisers_data.empty:
            # Заголовки
            headers = [advertisers_data.columns.tolist()]
            # Данные
            data = advertisers_data.values.tolist()
            
            values = headers + data
            self._write_values(spreadsheet_id, 'Advertisers!A1', values)
    
    def _fill_raw_data_sheet(self, spreadsheet_id: str, results: Dict):
        """Заполнение листа Raw Data"""
        # Если есть исходные данные
        pass
    
    def _fill_insights_sheet(self, spreadsheet_id: str, results: Dict):
        """Заполнение листа Insights"""
        recommendations = results.get('recommendations', [])
        
        values = [['Рекомендации']]
        for i, rec in enumerate(recommendations, 1):
            values.append([f"{i}. {rec}"])
        
        self._write_values(spreadsheet_id, 'Insights!A1', values)
    
    def _write_values(self, spreadsheet_id: str, range_name: str, values: List[List]):
        """Запись значений в таблицу"""
        try:
            body = {'values': values}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
        except HttpError as e:
            logger.error(f"✗ Ошибка записи в {range_name}: {e}")
    
    def export_dataframe(
        self,
        df: pd.DataFrame,
        spreadsheet_id: str,
        sheet_name: str = 'Sheet1'
    ):
        """
        Экспорт DataFrame в существующую таблицу
        
        Args:
            df: DataFrame для экспорта
            spreadsheet_id: ID таблицы
            sheet_name: название листа
        """
        if df.empty:
            logger.warning("DataFrame пустой, нечего экспортировать")
            return
        
        # Заголовки + данные
        values = [df.columns.tolist()] + df.values.tolist()
        
        try:
            self._write_values(spreadsheet_id, f'{sheet_name}!A1', values)
            logger.info(f"✓ Экспортировано {len(df)} строк в {sheet_name}")
        except Exception as e:
            logger.error(f"✗ Ошибка экспорта DataFrame: {e}")
    
    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Получение URL таблицы"""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


# ==================== CONVENIENCE FUNCTIONS ====================

def export_to_slides(analysis_results: Dict, title: str = None) -> Optional[str]:
    """
    Быстрый экспорт в Google Slides
    
    Args:
        analysis_results: результаты анализа
        title: название презентации
    
    Returns:
        URL презентации или None при ошибке
    """
    if not GOOGLE_API_AVAILABLE:
        logger.error("Google API недоступен")
        return None
    
    try:
        exporter = GoogleSlidesExporter()
        title = title or f"DSP Analytics - {datetime.now().strftime('%Y-%m-%d')}"
        presentation_id = exporter.create_presentation(title, analysis_results)
        url = exporter.get_presentation_url(presentation_id)
        logger.info(f"✓ Презентация: {url}")
        return url
    except Exception as e:
        logger.error(f"✗ Ошибка экспорта в Slides: {e}")
        return None


def export_to_sheets(analysis_results: Dict, title: str = None) -> Optional[str]:
    """
    Быстрый экспорт в Google Sheets
    
    Args:
        analysis_results: результаты анализа
        title: название таблицы
    
    Returns:
        URL таблицы или None при ошибке
    """
    if not GOOGLE_API_AVAILABLE:
        logger.error("Google API недоступен")
        return None
    
    try:
        exporter = GoogleSheetsExporter()
        title = title or f"DSP Analytics - {datetime.now().strftime('%Y-%m-%d')}"
        spreadsheet_id = exporter.create_spreadsheet(title, analysis_results)
        url = exporter.get_spreadsheet_url(spreadsheet_id)
        logger.info(f"✓ Таблица: {url}")
        return url
    except Exception as e:
        logger.error(f"✗ Ошибка экспорта в Sheets: {e}")
        return None


"""
Data loading: Excel/CSV files and public Google Sheets
"""
import re
import pandas as pd
import requests
from io import BytesIO, StringIO
from typing import Optional

import config


def _col_has_mojibake(df: pd.DataFrame) -> bool:
    """Check if any column name contains Latin Supplement mojibake (U+0080–U+00FF)."""
    for col in df.columns:
        if any('\u0080' <= c <= '\u00ff' for c in str(col)):
            return True
    return False


def load_file(file_obj, filename: str) -> pd.DataFrame:
    """Load Excel or CSV from a file-like object."""
    name = filename.lower()
    if name.endswith('.csv'):
        raw = file_obj.read()
        # Try each encoding; accept the first that parses AND has clean column names
        encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'cp1252', 'latin-1']
        last_error = None
        candidates = []
        for enc in encodings:
            try:
                df = pd.read_csv(StringIO(raw.decode(enc)), sep=None, engine='python')
                if df.empty:
                    continue
                if not _col_has_mojibake(df):
                    return df          # clean column names → correct encoding
                candidates.append(df)  # parseable but still mojibake — save as fallback
            except (UnicodeDecodeError, Exception) as e:
                last_error = e
                continue
        if candidates:
            return candidates[0]  # best we could do
        raise ValueError(f"Не удалось прочитать CSV: {last_error}")
    elif name.endswith(('.xlsx', '.xls')):
        engine = 'openpyxl' if name.endswith('.xlsx') else None
        xl = pd.ExcelFile(file_obj, engine=engine)
        return xl, xl.sheet_names  # return ExcelFile + sheet list for UI
    else:
        raise ValueError(f"Неподдерживаемый формат: {filename}")


def load_google_sheet(url: str) -> pd.DataFrame:
    """Load public Google Sheet by URL."""
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        raise ValueError("Не удалось извлечь ID таблицы из URL. Убедитесь что доступ открыт (Файл → Открыть доступ → Все у кого есть ссылка).")
    sheet_id = match.group(1)
    gid_match = re.search(r'gid=(\d+)', url)
    gid = gid_match.group(1) if gid_match else '0'
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(export_url, timeout=30)
    if resp.status_code == 403:
        raise ValueError("Нет доступа к таблице. Откройте доступ: Файл → Открыть доступ → Все у кого есть ссылка → Просматривающий.")
    resp.raise_for_status()
    # Try UTF-8 first; if column names still have mojibake, try cp1251
    raw = resp.content
    for enc in ('utf-8', 'utf-8-sig', 'cp1251'):
        try:
            df = pd.read_csv(BytesIO(raw), encoding=enc)
            if not df.empty and not _col_has_mojibake(df):
                return df
        except Exception:
            continue
    # Last resort
    return pd.read_csv(BytesIO(raw), encoding='utf-8', errors='replace')


def detect_columns_keyword(df: pd.DataFrame) -> dict:
    """
    Fallback keyword-based column detection.
    Returns {original_col: standard_field}.
    """
    mapping = {}
    used_standards = set()
    for orig_col in df.columns:
        col_lower = orig_col.lower().strip()
        for standard, keywords in config.STANDARD_COLS.items():
            if standard in used_standards:
                continue
            if col_lower in keywords or any(kw in col_lower for kw in keywords):
                mapping[orig_col] = standard
                used_standards.add(standard)
                break
    return mapping

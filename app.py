"""
Media Analytics — Streamlit app
Sources: Excel/CSV files and public Google Sheets
"""
import os
import streamlit as st
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

import config
from loader import load_file, load_google_sheet, detect_columns_keyword
from cleaner import check_quality, clean_data
from analyzer import aggregate, summary, anomalies
from charts import (bar_comparison, dynamics_line, pie_chart,
                    horizontal_bar, scatter_plot, funnel_chart)
from ai import LLMClient, _df_to_text, _prompt_qbr, SYSTEM_ANALYST

st.set_page_config(page_title="Media Analytics", layout="wide", page_icon="📊",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', Arial, sans-serif !important; }

[data-testid="stSidebar"] { min-width: 260px !important; max-width: 260px !important; }
[data-testid="stSidebar"] > div {
    background: var(--secondary-background-color) !important;
    border-right: 1px solid rgba(128,128,128,0.15) !important;
}
[data-testid="stSidebarCollapseButton"] {
    position: fixed !important; top: 0.5rem !important;
    left: 0.5rem !important; z-index: 999 !important;
}
[data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700 !important; white-space: nowrap; }
[data-testid="stMetricLabel"] { font-size: 0.72rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.6; }
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }
[data-testid="stTabs"] button { font-size: 0.85rem !important; font-weight: 500 !important; padding: 8px 14px !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #6366F1 !important; font-weight: 600 !important; border-bottom-color: #6366F1 !important; }
h1 { font-size: 1.6rem !important; font-weight: 700 !important; }
h2 { font-size: 1.2rem !important; font-weight: 600 !important; }
h3 { font-size: 1.0rem !important; font-weight: 600 !important; }
[data-testid="stButton"] > button[kind="primary"] {
    background: #4F46E5 !important; border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; letter-spacing: 0.01em !important; color: #ffffff !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #4338CA !important; color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(79,70,229,0.35) !important;
}
[data-testid="stButton"] > button:not([kind="primary"]) { border-radius: 8px !important; font-weight: 500 !important; }
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div,
[data-testid="stTextArea"] textarea { border-radius: 8px !important; font-size: 0.875rem !important; border-color: rgba(128,128,128,0.25) !important; }
[data-testid="stExpander"] { border: 1px solid rgba(128,128,128,0.2) !important; border-radius: 10px !important; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.875rem !important; }
[data-testid="stDataFrame"] { border-radius: 8px !important; overflow: hidden; border: 1px solid rgba(128,128,128,0.2) !important; }
hr { border-color: rgba(128,128,128,0.15) !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── helpers ───────────────────────────────────────────────

def _fmt_kpi(val: float, metric: str) -> str:
    if metric in ('ctr', 'viewability', 'vtr'):
        return f"{val:.2%}"
    if metric in ('cpm', 'cpc'):
        return f"{val:,.1f}"
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val/1_000:.1f}K"
    return f"{val:,.0f}"


def _to_xlsx(data: pd.DataFrame, has_advertiser: bool, has_format: bool) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name="Data")
        if has_advertiser:
            aggregate(data, ['advertiser']).to_excel(writer, index=False, sheet_name="By_Advertiser")
        if has_format:
            aggregate(data, ['format']).to_excel(writer, index=False, sheet_name="By_Format")
    return buf.getvalue()


def _to_html_report(md_text: str, title: str = "QBR Report") -> str:
    try:
        import markdown as mdlib
        body = mdlib.markdown(md_text, extensions=['tables', 'nl2br'])
    except Exception:
        body = f"<pre>{md_text}</pre>"
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>{title}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 960px; margin: 40px auto; padding: 24px; color: #1F2937; line-height: 1.6; }}
  h1 {{ font-size: 1.8rem; border-bottom: 3px solid #4F46E5; padding-bottom: 8px; color: #1F2937; }}
  h2 {{ font-size: 1.3rem; color: #4F46E5; margin-top: 2rem; }}
  h3 {{ font-size: 1.1rem; color: #374151; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.9rem; }}
  th {{ background: #4F46E5; color: #fff; padding: 8px 12px; text-align: left; }}
  td {{ border: 1px solid #E5E7EB; padding: 8px 12px; }}
  tr:nth-child(even) {{ background: #F9FAFB; }}
  strong {{ color: #1F2937; }}
  @media print {{ body {{ margin: 20px; }} }}
</style></head>
<body><h1>{title}</h1>{body}</body></html>"""


def _col_config_metrics(cols: list) -> dict:
    """Return column_config dict for metric columns."""
    cc = {}
    for c in cols:
        if c == 'ctr':          cc[c] = st.column_config.NumberColumn("CTR, %", format="%.2f")
        elif c == 'viewability': cc[c] = st.column_config.NumberColumn("Viewability, %", format="%.0f")
        elif c == 'vtr':         cc[c] = st.column_config.NumberColumn("VTR, %", format="%.0f")
        elif c in ('cpm','cpc'): cc[c] = st.column_config.NumberColumn(c.upper(), format="%.1f")
        elif c == 'TotalSum':    cc[c] = st.column_config.NumberColumn("Бюджет", format="%.1f")
        elif c == 'impressions': cc[c] = st.column_config.NumberColumn("Показы", format="%d")
        elif c == 'clicks':      cc[c] = st.column_config.NumberColumn("Клики", format="%d")
    return cc


def _prepare_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Multiply ratio metrics by 100 for table display."""
    df = df.copy()
    for c in df.columns:
        if c == 'ctr':          df[c] = (df[c] * 100).round(2)
        elif c == 'viewability': df[c] = (df[c] * 100).round(0)
        elif c == 'vtr':         df[c] = (df[c] * 100).round(0)
    return df


# ── caching ───────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_file(file_bytes: bytes, filename: str):
    return load_file(BytesIO(file_bytes), filename)


@st.cache_data(show_spinner=False)
def _load_gsheet(url: str) -> pd.DataFrame:
    return load_google_sheet(url)


@st.cache_data(show_spinner=False)
def _detect_cols_llm(col_tuple: tuple, sample_json: str,
                     api_key: str, provider: str, model: str) -> dict:
    try:
        return LLMClient(api_key, provider, model).detect_columns(list(col_tuple), sample_json)
    except Exception:
        return {}


# ── sidebar ───────────────────────────────────────────────

with st.sidebar:
    st.title("📊 Media Analytics")
    st.header("Данные")
    source = st.radio("Источник:", ["📁 Файл", "🔗 Google Sheets"], horizontal=True)

    raw_df: pd.DataFrame | None = None

    if source == "📁 Файл":
        uploaded = st.file_uploader("Excel или CSV", type=["xlsx", "xls", "csv"])
        if uploaded:
            with st.spinner("Загружаем файл…"):
                try:
                    file_bytes = uploaded.read()
                    _load_file.clear()
                    result = _load_file(file_bytes, uploaded.name)
                    if isinstance(result, tuple):
                        xl, sheet_names = result
                        if len(sheet_names) > 1:
                            sheet_mode = st.radio("Листы:", ["Все листы вместе"] + sheet_names, key="sheet_mode")
                            if sheet_mode == "Все листы вместе":
                                frames = [xl.parse(s).assign(_sheet=s) for s in sheet_names]
                                raw_df = pd.concat(frames, ignore_index=True)
                            else:
                                raw_df = xl.parse(sheet_mode)
                        else:
                            raw_df = xl.parse(sheet_names[0])
                    else:
                        raw_df = result
                    st.success(f"✅ {uploaded.name} — {len(raw_df):,} строк")
                except Exception as e:
                    st.error(f"Ошибка загрузки: {e}")
    else:
        gsheet_url = st.text_input("Ссылка на Google Sheets",
                                   placeholder="https://docs.google.com/spreadsheets/d/…")
        col_load, col_refresh = st.columns([3, 1])
        with col_load:
            if gsheet_url and st.button("Загрузить", use_container_width=True):
                with st.spinner("Загружаем таблицу…"):
                    try:
                        _load_gsheet.clear()
                        raw_df = _load_gsheet(gsheet_url)
                        st.session_state['gsheet_df'] = raw_df
                        st.session_state['gsheet_url'] = gsheet_url
                        st.success(f"✅ {len(raw_df):,} строк")
                    except Exception as e:
                        st.error(str(e))
        with col_refresh:
            if 'gsheet_df' in st.session_state and st.button("🔄", help="Обновить данные"):
                _load_gsheet.clear()
                try:
                    raw_df = _load_gsheet(st.session_state.get('gsheet_url', gsheet_url))
                    st.session_state['gsheet_df'] = raw_df
                    st.toast("Данные обновлены", icon="✅")
                except Exception as e:
                    st.error(str(e))
        if 'gsheet_df' in st.session_state and raw_df is None:
            raw_df = st.session_state['gsheet_df']

    st.divider()
    st.header("AI (необязательно)")
    provider = st.selectbox("Провайдер:", list(config.LLM_PROVIDERS.keys()))
    _default_key = os.getenv("MISTRAL_API_KEY", "")
    api_key = st.text_input("API Key", value=_default_key, type="password")
    provider_cfg = config.LLM_PROVIDERS[provider]
    if provider == "Custom (proxy)":
        custom_base_url = st.text_input("Base URL", placeholder="https://api.example.com/v1")
        llm_model = st.text_input("Модель", placeholder="gpt-4o-mini")
    else:
        custom_base_url = provider_cfg.get('base_url')
        llm_model = st.text_input("Модель", value=provider_cfg.get('default_model', ''))
    llm_available = bool(api_key)

    # Date range filter — populated after data is loaded
    if 'df_date_range' in st.session_state:
        st.divider()
        st.header("Фильтр дат")
        _dmin, _dmax = st.session_state['df_date_range']
        date_from = st.date_input("С:", value=_dmin, min_value=_dmin, max_value=_dmax, key="date_from")
        date_to   = st.date_input("По:", value=_dmax, min_value=_dmin, max_value=_dmax, key="date_to")
        st.session_state['active_date_from'] = pd.Timestamp(date_from)
        st.session_state['active_date_to']   = pd.Timestamp(date_to)

    # Format filter placeholder (populated below after df is built)
    _fmt_filter_placeholder = st.empty()


# ── empty state ───────────────────────────────────────────

if raw_df is None:
    st.title("📊 Media Analytics")
    st.markdown("Инструмент для анализа рекламных данных — графики, инсайты, QBR.")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Как начать")
        st.markdown("""
1. **Загрузите файл** — Excel (.xlsx) или CSV
2. **Или вставьте ссылку** на Google Sheets (открытый доступ)
3. **Проверьте маппинг** колонок — система определит автоматически
4. **Анализируйте** — дашборд, сравнения, AI инсайты, QBR
        """)
    with c2:
        st.markdown("### Поддерживаемые данные")
        st.markdown("""
- Показы, клики, CTR, CPM, CPC
- Бюджет / расходы
- Рекламодатели, кампании, форматы
- Баннерные размеры, даты
        """)
    st.stop()

# ── column mapping ────────────────────────────────────────

file_key = str(sorted(raw_df.columns.tolist()))
if 'col_map' not in st.session_state or st.session_state.get('col_map_key') != file_key:
    if llm_available:
        sample_json = raw_df.head(3).to_json(orient='records', force_ascii=False)
        llm_map = _detect_cols_llm(tuple(raw_df.columns.tolist()), sample_json,
                                    api_key, provider, llm_model)
    else:
        llm_map = {}
    kw_map = detect_columns_keyword(raw_df)
    st.session_state['col_map'] = {**kw_map, **llm_map}
    st.session_state['col_map_key'] = file_key

col_map = st.session_state['col_map']

with st.expander("⚙️ Маппинг колонок", expanded=(not bool(col_map))):
    st.caption("Система определила колонки автоматически. Исправьте если нужно.")
    standard_options = ['— пропустить —'] + list(config.STANDARD_COLS.keys())
    _map_df = pd.DataFrame([
        {"Исходная колонка": orig, "Стандартное поле": col_map.get(orig, '— пропустить —')}
        for orig in raw_df.columns
    ])
    _edited = st.data_editor(
        _map_df, use_container_width=True, hide_index=True, num_rows="fixed",
        column_config={
            "Исходная колонка": st.column_config.TextColumn(disabled=True, width="medium"),
            "Стандартное поле": st.column_config.SelectboxColumn(options=standard_options, width="medium"),
        },
        key="col_map_editor",
    )
    if st.button("Применить маппинг", type="primary"):
        new_map = {r["Исходная колонка"]: r["Стандартное поле"]
                   for _, r in _edited.iterrows() if r["Стандартное поле"] != '— пропустить —'}
        st.session_state['col_map'] = new_map
        col_map = new_map

# ── data cleaning ─────────────────────────────────────────

issues = check_quality(raw_df)
df = clean_data(raw_df, col_map)

if issues:
    with st.expander(f"{'🔴' if any(i.level == 'error' for i in issues) else '🟡'} Качество данных ({len(issues)} замечаний)"):
        for issue in issues:
            icon = "🔴" if issue.level == 'error' else "🟡" if issue.level == 'warning' else "ℹ️"
            st.markdown(f"{icon} {issue.message}")

# ── date range filter ─────────────────────────────────────

if 'date' in df.columns:
    _d_min, _d_max = df['date'].min().date(), df['date'].max().date()
    if st.session_state.get('df_date_range') != (_d_min, _d_max):
        st.session_state['df_date_range'] = (_d_min, _d_max)
        st.session_state['active_date_from'] = pd.Timestamp(_d_min)
        st.session_state['active_date_to']   = pd.Timestamp(_d_max)
        st.rerun()
    _af = st.session_state.get('active_date_from', pd.Timestamp(_d_min))
    _at = st.session_state.get('active_date_to',   pd.Timestamp(_d_max))
    df = df[(df['date'] >= _af) & (df['date'] <= _at)]

# ── resolved columns ──────────────────────────────────────

has_date       = 'date' in df.columns
has_advertiser = 'advertiser' in df.columns
has_spend      = 'TotalSum' in df.columns
has_format     = 'format' in df.columns
has_campaign   = 'campaign' in df.columns

dim_cols    = [c for c in ['advertiser', 'campaign', 'format', 'banner_size', 'product'] if c in df.columns]
metric_cols = [c for c in ['impressions', 'clicks', 'TotalSum', 'ctr', 'cpm', 'cpc', 'viewability', 'vtr'] if c in df.columns]

# Format filter in sidebar
_fmt_filter_val = None
if has_format:
    with _fmt_filter_placeholder.container():
        st.divider()
        st.header("Фильтры")
        _fmt_options = ['Все форматы'] + sorted(df['format'].dropna().unique().tolist())
        _fmt_chosen = st.selectbox("Формат:", _fmt_options, key="fmt_filter")
        if _fmt_chosen != 'Все форматы':
            _fmt_filter_val = _fmt_chosen

# ── tabs ──────────────────────────────────────────────────

tab_dash, tab_compare, tab_dynamics, tab_ai, tab_qbr = st.tabs([
    "📊 Дашборд", "🔍 Сравнение", "📈 Динамика", "🤖 AI Анализ", "📋 QBR",
])

# ═══════════════════════════════════════════════════
# TAB 1: DASHBOARD
# ═══════════════════════════════════════════════════
with tab_dash:
    selected_adv = st.session_state.get('selected_adv', None)

    df_dash = df.copy()
    if selected_adv and has_advertiser:
        df_dash = df_dash[df_dash['advertiser'] == selected_adv]
    if _fmt_filter_val and has_format:
        df_dash = df_dash[df_dash['format'] == _fmt_filter_val]

    # ── KPI cards ─────────────────────────────────
    stats = summary(df_dash)
    kpi_metrics = [
        ("💰 Бюджет",  stats['spend'],       'spend'),
        ("👁️ Показы",  stats['impressions'], 'impressions'),
        ("🖱️ Клики",   stats['clicks'],      'clicks'),
        ("📈 CTR",     stats['ctr'],         'ctr'),
        ("💵 CPM",     stats['cpm'],         'cpm'),
        ("🔢 CPC",     stats['cpc'],         'cpc'),
    ]
    _kpi_cols = st.columns(len(kpi_metrics))
    _kpi_strs = []
    for col_ui, (label, val, metric) in zip(_kpi_cols, kpi_metrics):
        display_val = _fmt_kpi(val, metric) if val > 0 else "—"
        col_ui.metric(label, display_val)
        _kpi_strs.append(f"{label.split()[-1]}: {display_val}")

    # Copy KPI button
    _kpi_text = " | ".join(_kpi_strs)
    st.markdown(
        f'<button onclick="navigator.clipboard.writeText(`{_kpi_text}`).then(()=>this.textContent=\'✅ Скопировано\').catch(()=>{{}}); setTimeout(()=>this.textContent=\'📋 Скопировать KPI\',2000)" '
        f'style="padding:4px 12px;border:1px solid rgba(128,128,128,0.3);border-radius:6px;background:none;cursor:pointer;font-size:0.78rem;margin-bottom:4px;">📋 Скопировать KPI</button>',
        unsafe_allow_html=True,
    )
    if selected_adv:
        st.caption(f"Фильтр: **{selected_adv}** — выберите «Все рекламодатели» для сброса")

    st.divider()

    # ── Budget charts: Pie + Treemap + Advertiser filter ──
    if has_advertiser and has_spend:
        adv_agg = aggregate(df, ['advertiser']).sort_values('TotalSum', ascending=False)

        adv_options = ['Все рекламодатели'] + adv_agg['advertiser'].tolist()
        current_idx = adv_options.index(selected_adv) if selected_adv in adv_options else 0
        chosen = st.selectbox("Рекламодатель:", adv_options, index=current_idx, key="adv_select",
                              help="Начните вводить название для фильтрации списка")
        new_val = None if chosen == 'Все рекламодатели' else chosen
        if new_val != st.session_state.get('selected_adv'):
            st.session_state['selected_adv'] = new_val
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(pie_chart(adv_agg, 'advertiser', 'TotalSum',
                                      'Распределение бюджета', selected_label=selected_adv),
                            use_container_width=True)
        with col2:
            if has_format:
                fmt_src = df_dash if selected_adv else df
                fmt_agg = aggregate(fmt_src, ['format']).sort_values('TotalSum', ascending=False)
                title_fmt = f"Форматы — {selected_adv}" if selected_adv else "Бюджет по форматам"
                st.plotly_chart(pie_chart(fmt_agg, 'format', 'TotalSum', title_fmt),
                                use_container_width=True)
            elif has_campaign:
                camp_agg = aggregate(df_dash, ['campaign']).nlargest(10, 'TotalSum')
                st.plotly_chart(horizontal_bar(camp_agg, 'campaign', 'TotalSum',
                                               title='ТОП кампаний по бюджету'),
                                use_container_width=True)

    # ── Drill-down: advertiser → campaigns / formats ──
    if selected_adv:
        st.subheader(f"Детализация — {selected_adv}")
        _drill_cols = st.columns(2)
        if has_campaign:
            camp_drill = aggregate(df_dash, ['campaign']).sort_values('TotalSum', ascending=False).head(10)
            with _drill_cols[0]:
                st.plotly_chart(horizontal_bar(camp_drill, 'campaign', 'TotalSum',
                                               title='Кампании по бюджету'),
                                use_container_width=True)
        if has_format:
            fmt_drill = aggregate(df_dash, ['format']).sort_values('TotalSum', ascending=False)
            with _drill_cols[1]:
                st.plotly_chart(pie_chart(fmt_drill, 'format', 'TotalSum', 'Форматы'),
                                use_container_width=True)

    # ── Scatter CTR vs CPM ────────────────────────
    _scatter_dim = next((c for c in ['advertiser', 'campaign'] if c in df_dash.columns), None)
    if _scatter_dim and 'ctr' in df_dash.columns and 'cpm' in df_dash.columns:
        _sc_agg = aggregate(df_dash, [_scatter_dim]).copy()
        _sc_agg['ctr_pct'] = _sc_agg['ctr'] * 100
        st.subheader("CTR vs CPM")
        st.caption("Размер пузыря = бюджет. Правый верхний угол = высокий CTR при низком CPM (лучшая эффективность).")
        st.plotly_chart(
            scatter_plot(_sc_agg, x='cpm', y='ctr_pct',
                         size='TotalSum' if has_spend else None,
                         color=_scatter_dim, title='CTR vs CPM',
                         x_label='CPM', y_label='CTR, %'),
            use_container_width=True,
        )

    # ── Display vs Video ──────────────────────────
    if has_format and 'impressions' in df.columns:
        fmt_agg = aggregate(df_dash, ['format'])
        fmt_agg['_fl'] = fmt_agg['format'].str.lower()
        display_df = fmt_agg[fmt_agg['_fl'].str.contains('display|баннер|banner|графика', na=False)]
        video_df   = fmt_agg[fmt_agg['_fl'].str.contains('video|видео|vid|ролик', na=False)]
        if not display_df.empty or not video_df.empty:
            st.subheader("Display vs Video")
            for seg_name, seg_df in [s for s in [("Display", display_df), ("Video", video_df)] if not s[1].empty]:
                imp   = seg_df['impressions'].sum()
                spend = seg_df['TotalSum'].sum() if has_spend else 0
                ctr   = (seg_df['clicks'].sum() / imp) if ('clicks' in seg_df.columns and imp > 0) else 0
                c1, c2, c3 = st.columns(3)
                c1.metric(f"👁️ {seg_name} Показы", f"{imp:,.0f}")
                c2.metric(f"💰 {seg_name} Бюджет", f"{spend:,.1f}")
                c3.metric(f"📈 {seg_name} CTR", f"{ctr:.2%}")

    # ── Top-5 / Bottom-5 CTR ──────────────────────
    _ctr_dim = next((c for c in ['campaign', 'advertiser'] if c in df_dash.columns), None)
    if _ctr_dim and 'ctr' in df_dash.columns:
        st.subheader("Топ-5 / Антитоп-5 по CTR")
        _ctr_agg = aggregate(df_dash, [_ctr_dim])
        if 'impressions' in _ctr_agg.columns:
            _ctr_agg = _ctr_agg[_ctr_agg['impressions'] >= 10_000]
        if len(_ctr_agg) >= 2:
            _tb_cols = [_ctr_dim, 'ctr'] + (['impressions'] if 'impressions' in _ctr_agg.columns else [])
            _top5 = _ctr_agg.nlargest(5, 'ctr')[_tb_cols].copy()
            _bot5 = _ctr_agg.nsmallest(5, 'ctr')[_tb_cols].copy()
            for _tdf in (_top5, _bot5):
                _tdf['ctr'] = (_tdf['ctr'] * 100).round(2)
            _col_cfg = {_ctr_dim: st.column_config.TextColumn(_ctr_dim, width="medium"),
                        'ctr': st.column_config.NumberColumn("CTR, %", format="%.2f", width="small"),
                        'impressions': st.column_config.NumberColumn("Показы", format="%d", width="small")}
            tc1, tc2 = st.columns(2)
            with tc1:
                st.caption("🏆 Топ-5")
                st.dataframe(_top5, use_container_width=True, hide_index=True, column_config=_col_cfg)
            with tc2:
                st.caption("⚠️ Антитоп-5")
                st.dataframe(_bot5, use_container_width=True, hide_index=True, column_config=_col_cfg)

    st.divider()

    # ── Funnel (if conversions available) ────────
    if any(c in df_dash.columns for c in ['post_click_conversions', 'revenue']):
        _funnel = funnel_chart(df_dash)
        if _funnel.data:
            st.plotly_chart(_funnel, use_container_width=True)

    # ── Data preview ──────────────────────────────
    _label = f"📋 Данные — {selected_adv} (первые 100 строк)" if selected_adv else "📋 Данные (первые 100 строк)"
    with st.expander(_label):
        _prev = _prepare_display_df(df_dash.head(100))
        st.dataframe(_prev, use_container_width=True,
                     column_config=_col_config_metrics(list(_prev.columns)))

    st.download_button(
        "📥 Скачать данные (.xlsx)",
        data=_to_xlsx(df_dash, has_advertiser, has_format),
        file_name="media_analytics_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ═══════════════════════════════════════════════════
# TAB 2: COMPARISON
# ═══════════════════════════════════════════════════
with tab_compare:
    if not dim_cols:
        st.info("Нет колонок-измерений (advertiser, campaign, format и т.д.) — проверьте маппинг.")
    else:
        c1, c2 = st.columns([1, 3])
        with c1:
            group_dim = st.selectbox("Разбивка по:", dim_cols)
            compare_metrics = st.multiselect(
                "Метрики:", metric_cols,
                default=[m for m in ['ctr', 'cpm', 'TotalSum'] if m in metric_cols][:3],
            )
            min_imp = st.number_input("Мин. показов:", value=0, step=1000)

        agg_df = aggregate(df, [group_dim])
        if min_imp > 0 and 'impressions' in agg_df.columns:
            agg_df = agg_df[agg_df['impressions'] >= min_imp]
        if compare_metrics:
            agg_df = agg_df.sort_values(compare_metrics[0], ascending=False)

        with c2:
            if compare_metrics:
                chart_df = agg_df.copy()
                _pct_map = {'ctr': 'CTR, %', 'viewability': 'Viewability, %', 'vtr': 'VTR, %'}
                chart_metrics = []
                for m in compare_metrics:
                    if m in _pct_map:
                        label = _pct_map[m]
                        chart_df[label] = (chart_df[m] * 100).round(2)
                        chart_metrics.append(label)
                    else:
                        chart_metrics.append(m)
                st.plotly_chart(
                    bar_comparison(chart_df, group_dim, chart_metrics,
                                   title=f"Сравнение по {group_dim}"),
                    use_container_width=True,
                )

        st.subheader("Таблица")
        _disp = _prepare_display_df(agg_df[[group_dim] + [c for c in metric_cols if c in agg_df.columns]])
        st.dataframe(_disp, use_container_width=True,
                     column_config=_col_config_metrics(list(_disp.columns)))

        # Anomalies
        if 'ctr' in agg_df.columns:
            def _is_anomaly(row):
                fmt_val = str(row.get('format', '')).lower() if 'format' in row else ''
                is_video = any(v in fmt_val for v in ['video', 'видео', 'vid'])
                lo = config.CTR_BENCHMARK_VIDEO if is_video else config.CTR_BENCHMARK
                hi = config.CTR_ANOMALY_HIGH_VIDEO if is_video else config.CTR_ANOMALY_HIGH_DISPLAY
                return row['ctr'] < lo or row['ctr'] > hi

            anom = agg_df[agg_df.apply(_is_anomaly, axis=1)] if has_format else anomalies(agg_df, 'ctr')
            if not anom.empty:
                with st.expander(f"⚠️ Аномалии CTR ({len(anom)}) — Display: 0.10–0.40%, Video: 0.40–1.50%"):
                    _anom_cols = [c for c in [group_dim, 'format', 'ctr', 'impressions'] if c in anom.columns]
                    _anom_disp = _prepare_display_df(anom[_anom_cols])
                    st.dataframe(_anom_disp, use_container_width=True, hide_index=True,
                                 column_config=_col_config_metrics(list(_anom_disp.columns)))

# ═══════════════════════════════════════════════════
# TAB 3: DYNAMICS
# ═══════════════════════════════════════════════════
with tab_dynamics:
    if not has_date:
        st.info("Колонка с датой не найдена. Настройте маппинг.")
    else:
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            period = st.selectbox("Период:", ["D — день", "W — неделя", "M — месяц", "Q — квартал"])
            period_code = period[0]
        with c2:
            dyn_metrics = st.multiselect(
                "Метрики:",
                [m for m in ['ctr', 'cpm', 'TotalSum', 'impressions', 'clicks'] if m in df.columns],
                default=[m for m in ['ctr', 'TotalSum'] if m in df.columns],
            )
        with c3:
            color_by_opt = ['— без разбивки —'] + [c for c in dim_cols if c != 'date']
            color_by = st.selectbox("Разбивка линий:", color_by_opt)
            if color_by == '— без разбивки —':
                color_by = None

        if dyn_metrics:
            dyn_df = df.copy()
            dyn_df['_period'] = dyn_df['date'].dt.to_period(period_code)
            dyn_agg = aggregate(dyn_df, ([color_by, '_period'] if color_by else ['_period']))
            dyn_agg['_period'] = dyn_agg['_period'].astype(str)
            dyn_agg = dyn_agg.sort_values('_period')

            # Benchmark lines for CTR
            _benchmarks = []
            if 'ctr' in dyn_metrics and not color_by:
                _benchmarks = [
                    ("CTR Display норма", config.CTR_BENCHMARK, "#F59E0B"),
                    ("CTR Video норма", config.CTR_BENCHMARK_VIDEO, "#10B981"),
                ]

            st.plotly_chart(
                dynamics_line(dyn_agg, '_period', dyn_metrics, color_by=color_by,
                              title="Динамика метрик", benchmarks=_benchmarks),
                use_container_width=True,
            )

            # Period-over-period delta
            if len(dyn_agg['_period'].unique()) >= 2 and not color_by:
                st.subheader("Последний период vs предыдущий")
                last, prev = dyn_agg.iloc[-1], dyn_agg.iloc[-2]
                dcols = st.columns(len(dyn_metrics))
                for col_ui, m in zip(dcols, dyn_metrics):
                    if m in last and m in prev:
                        denom = abs(prev[m]) if prev[m] != 0 else 1
                        delta = (last[m] - prev[m]) / denom
                        fmt = '{:.2%}' if m == 'ctr' else '{:,.0f}'
                        col_ui.metric(m.upper(), fmt.format(last[m]), delta=f"{delta:+.1%}")

        st.divider()

        # ── Two-period comparison ─────────────────────
        st.subheader("Сравнение двух периодов")
        _min_d, _max_d = df['date'].min().date(), df['date'].max().date()
        _mid_d = _min_d + (_max_d - _min_d) // 2
        pc1, pc2 = st.columns(2)
        with pc1:
            st.caption("Период A")
            pa_from = st.date_input("С:", value=_min_d, min_value=_min_d, max_value=_max_d, key="pa_from")
            pa_to   = st.date_input("По:", value=_mid_d, min_value=_min_d, max_value=_max_d, key="pa_to")
        with pc2:
            st.caption("Период B")
            pb_from = st.date_input("С:", value=_mid_d, min_value=_min_d, max_value=_max_d, key="pb_from")
            pb_to   = st.date_input("По:", value=_max_d, min_value=_min_d, max_value=_max_d, key="pb_to")

        if st.button("Сравнить периоды", type="primary"):
            df_a = df[(df['date'] >= pd.Timestamp(pa_from)) & (df['date'] <= pd.Timestamp(pa_to))]
            df_b = df[(df['date'] >= pd.Timestamp(pb_from)) & (df['date'] <= pd.Timestamp(pb_to))]
            if df_a.empty or df_b.empty:
                st.warning("Один из периодов не содержит данных.")
            else:
                sa, sb = summary(df_a), summary(df_b)
                _cmp_rows = []
                for m_key, m_label in [('spend','Бюджет'),('impressions','Показы'),('clicks','Клики'),
                                        ('ctr','CTR'),('cpm','CPM'),('cpc','CPC')]:
                    va, vb = sa[m_key], sb[m_key]
                    denom = abs(va) if va != 0 else 1
                    delta = (vb - va) / denom
                    _cmp_rows.append({
                        'Метрика': m_label,
                        f'A ({pa_from}–{pa_to})': _fmt_kpi(va, m_key),
                        f'B ({pb_from}–{pb_to})': _fmt_kpi(vb, m_key),
                        'Δ (B vs A)': f"{delta:+.1%}",
                    })
                st.dataframe(pd.DataFrame(_cmp_rows), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════
# TAB 4: AI ANALYSIS
# ═══════════════════════════════════════════════════
with tab_ai:
    if not llm_available:
        st.info("Введите API Key в боковой панели для использования AI анализа.")
    else:
        analysis_type = st.selectbox("Тип анализа:", [
            "🔬 Универсальный анализ", "📊 Инсайты и аномалии",
            "📈 Тренды и динамика", "💡 Оптимизация бюджета",
            "📝 Executive Summary", "❓ Свой вопрос",
        ])
        custom_q = ""
        if analysis_type == "❓ Свой вопрос":
            custom_q = st.text_area("Ваш вопрос:", height=100,
                                    placeholder='"сравни только video форматы", "найди аномалии за Q3"')

        if st.button("Запустить анализ", type="primary", use_container_width=True):
            type_map = {
                "🔬 Универсальный анализ": "insights", "📊 Инсайты и аномалии": "insights",
                "📈 Тренды и динамика": "trends", "💡 Оптимизация бюджета": "budget",
                "📝 Executive Summary": "summary", "❓ Свой вопрос": "custom",
            }
            prompt_type = type_map[analysis_type]

            dfs = {"Общие данные": df}
            if has_advertiser:
                dfs["По рекламодателям"] = aggregate(df, ['advertiser'])
            if has_date:
                _d = df.copy()
                _d['period'] = _d['date'].dt.to_period('M')
                dfs["Динамика по месяцам"] = aggregate(_d, ['period']).assign(period=lambda x: x['period'].astype(str))

            try:
                llm = LLMClient(api_key, provider, llm_model,
                                base_url=custom_base_url if provider == "Custom (proxy)" else None)
                _placeholder = st.empty()
                _full = ""
                with st.spinner(""):
                    for _chunk in llm.stream_analyze(dfs, prompt_type, custom_q):
                        _full += _chunk
                        _placeholder.markdown(_full + "▌")
                _placeholder.markdown(_full)

                history = st.session_state.get('ai_history', [])
                history.insert(0, {'label': analysis_type, 'result': _full})
                st.session_state['ai_history'] = history[:3]
                st.session_state['ai_just_ran'] = True

                _xlsx_buf = BytesIO()
                pd.DataFrame([{"Анализ": _full}]).to_excel(_xlsx_buf, index=False)
                st.download_button("📥 Скачать анализ (.xlsx)", _xlsx_buf.getvalue(),
                                   file_name="analysis.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"Ошибка: {e}")

        # History (previous runs)
        elif st.session_state.get('ai_history'):
            history = st.session_state['ai_history']
            st.markdown("---")
            if len(history) == 1:
                st.markdown(history[0]['result'])
                _xlsx_buf = BytesIO()
                pd.DataFrame([{"Анализ": history[0]['result']}]).to_excel(_xlsx_buf, index=False)
                st.download_button("📥 Скачать (.xlsx)", _xlsx_buf.getvalue(),
                                   file_name="analysis.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl_ai_0")
            else:
                _htabs = st.tabs([f"#{i+1} {h['label']}" for i, h in enumerate(history)])
                for _ht, _h in zip(_htabs, history):
                    with _ht:
                        st.markdown(_h['result'])
                        _xlsx_buf = BytesIO()
                        pd.DataFrame([{"Анализ": _h['result']}]).to_excel(_xlsx_buf, index=False)
                        st.download_button("📥 Скачать (.xlsx)", _xlsx_buf.getvalue(),
                                           file_name="analysis.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           key=f"dl_ai_{id(_h)}")

# ═══════════════════════════════════════════════════
# TAB 5: QBR
# ═══════════════════════════════════════════════════
with tab_qbr:
    st.subheader("Quarterly Business Review")
    st.caption("Профессиональный отчёт для клиента")

    if not llm_available:
        st.info("Введите API Key в боковой панели для генерации QBR.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            client_name = st.text_input("Клиент / проект", placeholder="BRAND Q1 2025")
        with c2:
            period_label = st.text_input("Период", placeholder="Q1 2025 / январь–март 2025")
        with c3:
            qbr_style = st.selectbox("Стиль:", ["Краткий", "Детальный", "Для клиента"])

        extra_context = st.text_area("Дополнительный контекст:",
                                     placeholder="Цели кампании, KPI, особенности рынка…", height=80)

        if st.button("Сгенерировать QBR", type="primary", use_container_width=True):
            dfs = {"Сводные данные": df}
            if has_advertiser: dfs["По рекламодателям"] = aggregate(df, ['advertiser'])
            if has_format:     dfs["По форматам"] = aggregate(df, ['format'])
            if has_date:
                _d = df.copy()
                _d['period'] = _d['date'].dt.to_period('M')
                dfs["Динамика по месяцам"] = aggregate(_d, ['period']).assign(period=lambda x: x['period'].astype(str))
            if 'banner_size' in df.columns:
                dfs["По баннерным размерам"] = aggregate(df, ['banner_size'])

            context_prefix = ""
            if client_name or period_label:
                context_prefix = f"Клиент: {client_name or '—'}. Период: {period_label or '—'}.\n"
            if extra_context:
                context_prefix += f"Контекст: {extra_context}\n"

            parts = ([context_prefix] if context_prefix else []) + [
                f"=== {name} ===\n{_df_to_text(d)}" for name, d in dfs.items() if not d.empty
            ]
            _style_hints = {
                "Краткий": " Пиши кратко — не более 500 слов, только самое важное.",
                "Детальный": " Пиши подробно — разверни каждый раздел с деталями.",
                "Для клиента": " Пиши для клиента без жаргона, акцент на результаты и пользу.",
            }
            user_msg = _prompt_qbr() + _style_hints.get(qbr_style, "") + "\n\nДанные:\n" + "\n\n".join(parts)

            try:
                llm = LLMClient(api_key, provider, llm_model,
                                base_url=custom_base_url if provider == "Custom (proxy)" else None)
                st.markdown("---")
                _placeholder = st.empty()
                _full = ""
                with st.spinner(""):
                    for _chunk in llm.stream_chat(user_msg,
                                                  system=SYSTEM_ANALYST + " Составь профессиональный QBR.",
                                                  max_tokens=4500):
                        _full += _chunk
                        _placeholder.markdown(_full + "▌")
                _placeholder.markdown(_full)

                st.session_state['qbr_result'] = _full
                st.session_state['qbr_client'] = client_name

                _xlsx_buf = BytesIO()
                pd.DataFrame([{"QBR": _full}]).to_excel(_xlsx_buf, index=False)
                st.download_button("📥 Скачать QBR (.xlsx)", _xlsx_buf.getvalue(),
                                   file_name=f"QBR_{client_name or 'report'}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"Ошибка: {e}")

        elif 'qbr_result' in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state['qbr_result'])
            _cn = st.session_state.get('qbr_client', 'report')
            _xlsx_buf = BytesIO()
            pd.DataFrame([{"QBR": st.session_state['qbr_result']}]).to_excel(_xlsx_buf, index=False)
            st.download_button("📥 Скачать QBR (.xlsx)", _xlsx_buf.getvalue(),
                               file_name=f"QBR_{_cn}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="qbr_dl_xlsx")

# ═══════════════════════════════════════════════════

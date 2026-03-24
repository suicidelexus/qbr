"""
DSP Analytics Platform — Streamlit Dashboard
QBR / Competitive Analysis / LLM Insights
"""
import streamlit as st
import pandas as pd
from processing_layer import DataProcessor, AnalysisEngine
from visualization import ChartGenerator
import config

# ── Page config ──
st.set_page_config(page_title="DSP Analytics Platform", page_icon="📊", layout="wide")
st.title("📊 DSP Analytics Platform")

# ── helpers ──
processor = DataProcessor()
chart_gen = ChartGenerator()

PERF_METRICS = ['impressions', 'clicks', 'ctr', 'cpc', 'cpm',
                'viewability', 'vtr', 'frequency', 'reach', 'views']


def _available(df, cols):
    return [c for c in cols if c in df.columns]


def format_metric(value, metric_name):
    """Форматирование метрики в зависимости от типа"""
    if pd.isna(value):
        return "-"
    
    metric_lower = metric_name.lower()
    
    # CTR, VTR - в процентах (умножить на 100 и добавить %)
    if metric_lower in ['ctr', 'vtr']:
        return f"{value * 100:.2f}%"
    
    # Viewability - в процентах, округлить до целого
    if metric_lower == 'viewability':
        return f"{value * 100:.0f}%"
    
    # TotalSum, impressions, clicks, reach - целые числа с разделителями
    if metric_lower in ['totalsum', 'impressions', 'clicks', 'reach', 'views']:
        return f"{value:,.0f}"
    
    # CPM, CPC - 1 знак после запятой
    if metric_lower in ['cpm', 'cpc']:
        return f"{value:.1f}"
    
    # Frequency - 1 знак после запятой
    if metric_lower == 'frequency':
        return f"{value:.1f}"
    
    # По умолчанию - 2 знака
    if isinstance(value, float):
        return f"{value:.2f}"
    
    return str(value)


def format_dataframe(df, exclude_cols=None):
    """Форматирует DataFrame с правильным отображением метрик"""
    if exclude_cols is None:
        exclude_cols = []
    
    df_formatted = df.copy()
    
    for col in df_formatted.columns:
        if col in exclude_cols:
            continue
        if pd.api.types.is_numeric_dtype(df_formatted[col]):
            df_formatted[col] = df_formatted[col].apply(lambda x: format_metric(x, col))
    
    return df_formatted


# ═══════════════════════════════════════
#              SIDEBAR
# ═══════════════════════════════════════

# — API credentials (multi) —
st.sidebar.header("🔑 API Credentials")

if 'credentials' not in st.session_state:
    st.session_state['credentials'] = []

with st.sidebar.expander("Добавить credential", expanded=not st.session_state['credentials']):
    _label = st.text_input("Название *", placeholder="e.g. Agency A", key="_cred_label")
    _cid = st.text_input("Client ID *", key="_cred_cid")
    _skey = st.text_input("Secret Key *", type="password", key="_cred_skey")
    if st.button("➕ Добавить"):
        if _label and _cid and _skey:
            st.session_state['credentials'].append(
                {'advertiser': _label, 'client_id': _cid, 'secret_key': _skey})
            st.rerun()
        else:
            st.error("Заполните все поля")

for i, cr in enumerate(st.session_state['credentials']):
    c1, c2 = st.sidebar.columns([5, 1])
    c1.markdown(f"✅ **{cr['advertiser']}**")
    if c2.button("✕", key=f"rm_{i}"):
        st.session_state['credentials'].pop(i)
        st.rerun()

# — LLM settings (Groq) —
st.sidebar.markdown("---")
st.sidebar.header("🤖 Groq LLM")
with st.sidebar.expander("Настройки", expanded=False):
    llm_key = st.text_input(
        "API Key ([получить бесплатно](https://console.groq.com/keys))", 
        type="password",
        value=st.session_state.get('llm_key', config.GROQ_API_KEY or '')
    )
    
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
    llm_model = st.selectbox(
        "Модель",
        models,
        index=models.index(config.GROQ_MODEL) if config.GROQ_MODEL in models else 0
    )
    
    if st.button("💾 Сохранить"):
        st.session_state['llm_key'] = llm_key
        st.session_state['llm_model'] = llm_model
        st.success("✓ Сохранено!")

# — Data loading —
st.sidebar.markdown("---")
st.sidebar.header("📥 Загрузка данных")
days = st.sidebar.slider("Период (дней):", 1, 180, 90)

if st.sidebar.button("📥 Загрузить данные", type="primary",
                     disabled=not st.session_state['credentials']):
    from datetime import datetime, timedelta

    creds = st.session_state['credentials']
    end = datetime.now().date()
    start = end - timedelta(days=days)

    if len(creds) == 1:
        # single credential — use DSPClient directly
        from data_layer import DSPClient
        cr = creds[0]
        client = DSPClient(client_id=cr['client_id'], secret_key=cr['secret_key'])
        progress = st.sidebar.progress(0, text="Загрузка...")

        def _cb(idx, total, name, split):
            progress.progress(int(idx / max(total, 1) * 100),
                              text=f"{name} ({split}) {idx+1}/{total}")

        with st.spinner("Загрузка..."):
            all_data = client.get_all_splits_data(
                start.isoformat(), end.isoformat(), progress_callback=_cb)
        progress.progress(100, "Готово!")
    else:
        # multi credential
        from multi_advertiser import MultiAdvertiserManager
        mgr = MultiAdvertiserManager(credentials=creds)
        progress = st.sidebar.progress(0, text="Загрузка...")

        def _cb_multi(idx, total, label):
            progress.progress(int(idx / max(total, 1) * 100), text=f"{label} {idx+1}/{total}")

        with st.spinner("Загрузка от всех credentials..."):
            all_data = mgr.load_all_splits(start.isoformat(), end.isoformat(),
                                           progress_callback=_cb_multi)
        progress.progress(100, "Готово!")

    st.session_state['df_day'] = all_data.get('day', pd.DataFrame())
    st.session_state['df_bt'] = all_data.get('banner_type', pd.DataFrame())
    st.session_state['df_bs'] = all_data.get('banner_size', pd.DataFrame())
    st.sidebar.success(
        f"Day: {len(st.session_state['df_day'])} | "
        f"BT: {len(st.session_state['df_bt'])} | "
        f"BS: {len(st.session_state['df_bs'])}")
    st.rerun()

# demo
if st.sidebar.button("🎲 Демо данные"):
    import numpy as np
    dates = pd.date_range('2024-10-01', '2024-12-31', freq='D')
    advs = ['Advertiser A', 'Advertiser B', 'Advertiser C']
    bts = ['display', 'video', 'native']
    bss_p = config.BANNER_SIZE_PRIMARY
    bss_s = config.BANNER_SIZE_SECONDARY
    rows_d, rows_bt, rows_bs = [], [], []
    for d in dates:
        for a in advs:
            imp = np.random.randint(10000, 80000)
            rows_d.append({'date': d, 'advertiser': a, 'impressions': imp,
                           'clicks': int(imp * np.random.uniform(.001, .005)),
                           'TotalSum': imp * np.random.uniform(1, 5) / 1000,
                           'viewability': np.random.uniform(.6, .9),
                           'frequency': np.random.uniform(1, 4)})
    for a in advs:
        for bt in bts:
            imp = np.random.randint(100000, 500000)
            rows_bt.append({'advertiser': a, 'banner_type': bt, 'impressions': imp,
                            'clicks': int(imp * np.random.uniform(.001, .005)),
                            'TotalSum': imp * np.random.uniform(1, 5) / 1000,
                            'viewability': np.random.uniform(.6, .9)})
    for a in advs:
        for bs in bss_p + bss_s + ['other_size']:
            imp = np.random.randint(5000, 150000)
            rows_bs.append({'advertiser': a, 'banner_size': bs, 'impressions': imp,
                            'clicks': int(imp * np.random.uniform(.001, .004)),
                            'TotalSum': imp * np.random.uniform(1, 4) / 1000,
                            'viewability': np.random.uniform(.55, .85)})
    st.session_state['df_day'] = pd.DataFrame(rows_d)
    st.session_state['df_bt'] = pd.DataFrame(rows_bt)
    st.session_state['df_bs'] = pd.DataFrame(rows_bs)
    st.rerun()

# — Загрузка из файла (Excel / Google Sheets) —
st.sidebar.markdown("---")
st.sidebar.header("📁 Загрузка из файла")

with st.sidebar.expander("Excel / CSV / Google Sheets", expanded=False):
    
    # --- EXCEL / CSV ---
    uploaded_file = st.file_uploader(
        "📎 Загрузить Excel или CSV",
        type=['xlsx', 'xls', 'csv'],
        key="file_uploader"
    )
    
    # Сохраняем загруженный файл в session_state
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state['uploaded_df'] = pd.read_csv(uploaded_file)
            else:
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("Лист:", sheet_names, key="sheet_select")
                else:
                    selected_sheet = sheet_names[0]
                st.session_state['uploaded_df'] = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            st.session_state['uploaded_name'] = uploaded_file.name
        except Exception as e:
            st.error(f"Ошибка чтения файла: {e}")
    
    # --- GOOGLE SHEETS ---
    st.markdown("---")
    st.markdown("**Google Sheets:**")
    gsheet_url = st.text_input(
        "Ссылка на таблицу",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        key="gsheet_url",
        label_visibility="collapsed"
    )
    
    if gsheet_url and st.button("📥 Загрузить из Google Sheets"):
        try:
            import ssl
            import urllib.request
            import io
            
            if '/edit' in gsheet_url:
                csv_url = gsheet_url.split('/edit')[0] + '/export?format=csv'
            elif '/d/' in gsheet_url:
                sheet_id = gsheet_url.split('/d/')[1].split('/')[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            else:
                csv_url = gsheet_url
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(csv_url, context=ssl_context) as response:
                st.session_state['uploaded_df'] = pd.read_csv(io.BytesIO(response.read()))
                st.session_state['uploaded_name'] = "Google Sheets"
            st.success("✓ Данные загружены из Google Sheets")
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка: {e}")
    
    # Если есть загруженные данные - показываем их
    if 'uploaded_df' in st.session_state and st.session_state['uploaded_df'] is not None:
        df_source = st.session_state['uploaded_df']
        source_name = st.session_state.get('uploaded_name', 'Файл')
        
        st.success(f"✓ {source_name}: {len(df_source)} строк × {len(df_source.columns)} колонок")
        
        # Превью данных
        st.markdown("**Превью:**")
        st.dataframe(df_source.head(5), use_container_width=True)
        
        # Автоопределение колонок
        def auto_detect_column(df, keywords):
            for col in df.columns:
                col_lower = str(col).lower()
                for kw in keywords:
                    if kw in col_lower:
                        return col
            return None
        
        detected = {
            'date': auto_detect_column(df_source, ['date', 'дата', 'день', 'day', 'period', 'период']),
            'advertiser': auto_detect_column(df_source, ['advertiser', 'рекламодатель', 'клиент', 'client', 'account', 'аккаунт', 'name', 'название', 'campaign', 'кампания']),
            'impressions': auto_detect_column(df_source, ['impression', 'показ', 'imps', 'views', 'просмотр']),
            'clicks': auto_detect_column(df_source, ['click', 'клик', 'переход']),
            'spend': auto_detect_column(df_source, ['spend', 'cost', 'расход', 'бюджет', 'budget', 'sum', 'сумма', 'totalsum', 'total']),
            'ctr': auto_detect_column(df_source, ['ctr']),
            'cpm': auto_detect_column(df_source, ['cpm']),
            'cpc': auto_detect_column(df_source, ['cpc']),
        }
        
        st.markdown("**Найденные колонки:**")
        found = [f"{k}: `{v}`" for k, v in detected.items() if v]
        if found:
            st.markdown(", ".join(found))
        else:
            st.markdown("_(автоопределение не сработало)_")
        
        # Кнопка использования данных
        if st.button("✅ Использовать эти данные", type="primary", key="use_data_btn"):
            df_mapped = df_source.copy()
            
            # Переименовываем найденные колонки
            rename_map = {}
            if detected['date']:
                rename_map[detected['date']] = 'date'
            if detected['advertiser']:
                rename_map[detected['advertiser']] = 'advertiser'
            if detected['impressions']:
                rename_map[detected['impressions']] = 'impressions'
            if detected['clicks']:
                rename_map[detected['clicks']] = 'clicks'
            if detected['spend']:
                rename_map[detected['spend']] = 'TotalSum'
            if detected['ctr']:
                rename_map[detected['ctr']] = 'ctr'
            if detected['cpm']:
                rename_map[detected['cpm']] = 'cpm'
            if detected['cpc']:
                rename_map[detected['cpc']] = 'cpc'
            
            df_mapped = df_mapped.rename(columns=rename_map)
            
            # Преобразуем дату
            if 'date' in df_mapped.columns:
                df_mapped['date'] = pd.to_datetime(df_mapped['date'], errors='coerce')
            
            # Конвертируем числовые колонки
            numeric_cols = ['impressions', 'clicks', 'TotalSum', 'ctr', 'cpm', 'cpc', 'viewability', 'vtr', 'frequency', 'reach']
            for col in numeric_cols:
                if col in df_mapped.columns:
                    df_mapped[col] = pd.to_numeric(df_mapped[col], errors='coerce').fillna(0)
            
            # Если нет advertiser - создаём дефолтный
            if 'advertiser' not in df_mapped.columns:
                df_mapped['advertiser'] = source_name
            
            # Рассчитываем CTR если нет
            if 'ctr' not in df_mapped.columns and 'clicks' in df_mapped.columns and 'impressions' in df_mapped.columns:
                df_mapped['ctr'] = df_mapped['clicks'] / df_mapped['impressions'].replace(0, 1)
            
            # Сохраняем
            st.session_state['df_day'] = df_mapped
            st.session_state['df_bt'] = pd.DataFrame()
            st.session_state['df_bs'] = pd.DataFrame()
            
            # Очищаем uploaded_df
            del st.session_state['uploaded_df']
            if 'uploaded_name' in st.session_state:
                del st.session_state['uploaded_name']
            
            st.success("✅ Данные загружены! Перезагрузка...")
            st.rerun()
        
        # Кнопка очистки
        if st.button("🗑️ Очистить загруженный файл", key="clear_upload"):
            del st.session_state['uploaded_df']
            if 'uploaded_name' in st.session_state:
                del st.session_state['uploaded_name']
            st.rerun()

if st.sidebar.button("🗑️ Очистить"):
    for k in ('df_day', 'df_bt', 'df_bs'):
        st.session_state.pop(k, None)
    st.rerun()


# ═══════════════════════════════════════
#            MAIN CONTENT
# ═══════════════════════════════════════

df_day = st.session_state.get('df_day', pd.DataFrame())
df_bt = st.session_state.get('df_bt', pd.DataFrame())
df_bs = st.session_state.get('df_bs', pd.DataFrame())

if df_day.empty and df_bt.empty:
    st.info("👈 Добавьте API credentials и загрузите данные")
    st.stop()

# derive metrics
if not df_day.empty:
    df_day = processor.calculate_derived_metrics(df_day)
if not df_bt.empty:
    df_bt = processor.calculate_derived_metrics(df_bt)
if not df_bs.empty:
    df_bs = processor.calculate_derived_metrics(df_bs)

main_df = df_day if not df_day.empty else df_bt

# ── summary metrics ──
st.header("📈 Сводка")
mc = st.columns(5)
i = 0
for col, label, fmt in [
    ('impressions', 'Impressions', '{:,.0f}'),
    ('clicks', 'Clicks', '{:,.0f}'),
    ('ctr', 'CTR', '{:.3%}'),
    ('TotalSum', 'Бюджет', '{:,.0f}'),
    ('reach', 'Reach', '{:,.0f}'),
]:
    if col in main_df.columns and i < 5:
        val = main_df[col].mean() if col == 'ctr' else main_df[col].sum()
        mc[i].metric(label, fmt.format(val))
        i += 1

if 'advertiser' in main_df.columns:
    st.caption(f"👥 {main_df['advertiser'].nunique()} рекламодателей")

# ── TABS ──
tab_names = ["📊 Advertisers", "📈 Динамика", "📐 BannerSize",
             "🔀 Мульти-сравнение", "🤖 AI / QBR"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)

# ─────────── TAB 1: Advertisers (TotalSum по месяцам) ───────────
with tab1:
    st.subheader("Рекламодатели — расход по месяцам")

    if not df_day.empty and 'date' in df_day.columns:
        engine = AnalysisEngine(df_day)
        dyn = engine.dynamics('M', per_advertiser=True)

        if not dyn.empty and 'TotalSum' in dyn.columns:
            adv_col = next((c for c in ('advertiser', 'advertiser_id') if c in dyn.columns), None)

            if adv_col:
                # Выбор рекламодателей для сравнения
                all_advs = sorted(dyn[adv_col].unique().tolist())
                selected_advs = st.multiselect(
                    "Выберите рекламодателей для сравнения:",
                    all_advs,
                    default=all_advs[:min(3, len(all_advs))],
                    key="tab1_advs"
                )
                
                if selected_advs:
                    dyn_filtered = dyn[dyn[adv_col].isin(selected_advs)]
                    
                    # Общая динамика расхода (сумма по всем выбранным)
                    total_by_period = dyn_filtered.groupby('period')['TotalSum'].sum().reset_index()
                    total_change = ""
                    if len(total_by_period) >= 2:
                        first_val = total_by_period['TotalSum'].iloc[0]
                        last_val = total_by_period['TotalSum'].iloc[-1]
                        if first_val > 0:
                            change_pct = (last_val - first_val) / first_val * 100
                            total_change = f" | Динамика: {change_pct:+.1f}%"
                    
                    st.markdown(f"**Общий расход выбранных: {dyn_filtered['TotalSum'].sum():,.0f}**{total_change}")
                    
                    # Отдельный график для каждого рекламодателя (по 2 в строку)
                    for i in range(0, len(selected_advs), 2):
                        cols = st.columns(2)
                        for j, col in enumerate(cols):
                            if i + j < len(selected_advs):
                                adv = selected_advs[i + j]
                                adv_data = dyn_filtered[dyn_filtered[adv_col] == adv]
                                with col:
                                    # Расчёт динамики
                                    if len(adv_data) >= 2:
                                        first = adv_data['TotalSum'].iloc[0]
                                        last = adv_data['TotalSum'].iloc[-1]
                                        change = ((last - first) / first * 100) if first > 0 else 0
                                        trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                                        title = f"{adv} {trend} {change:+.1f}%"
                                    else:
                                        title = adv
                                    
                                    import plotly.express as px
                                    fig = px.line(adv_data, x='period', y='TotalSum', markers=True)
                                    fig.update_layout(
                                        title=dict(text=title, font=dict(size=13)),
                                        showlegend=False,
                                        height=250,
                                        margin=dict(l=40, r=20, t=40, b=30),
                                        xaxis_title=None,
                                        yaxis_title=None,
                                        hovermode='x unified',
                                    )
                                    fig.update_traces(
                                        hovertemplate='%{y:,.0f}<extra></extra>',
                                        line=dict(width=2),
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                    # Таблица с диапазоном для каждого рекламодателя
                    st.markdown("---")
                    st.markdown("### 📋 Сводка по рекламодателям")
                    
                    summary_table = []
                    for adv in selected_advs:
                        adv_data = dyn_filtered[dyn_filtered[adv_col] == adv].sort_values('period')
                        if len(adv_data) >= 1:
                            first_period = adv_data['period'].iloc[0]
                            last_period = adv_data['period'].iloc[-1]
                            first_spend = adv_data['TotalSum'].iloc[0]
                            last_spend = adv_data['TotalSum'].iloc[-1]
                            total_spend = adv_data['TotalSum'].sum()
                            
                            if len(adv_data) >= 2 and first_spend > 0:
                                change_pct = ((last_spend - first_spend) / first_spend * 100)
                                trend = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
                            else:
                                change_pct = 0
                                trend = "➡️"
                            
                            summary_table.append({
                                'Рекламодатель': adv,
                                'Период': f"{first_period} → {last_period}",
                                first_period: f"{first_spend:,.0f}",
                                last_period: f"{last_spend:,.0f}",
                                'Изменение': f"{trend} {change_pct:+.1f}%",
                                'Итого': f"{total_spend:,.0f}",
                            })
                    
                    if summary_table:
                        st.dataframe(pd.DataFrame(summary_table), use_container_width=True)
                    
                    # Детальная таблица
                    with st.expander("📊 Детальные данные по периодам"):
                        show = _available(dyn_filtered, [adv_col, 'period', 'TotalSum'])
                        if show:
                            display_df = dyn_filtered[show].sort_values(['period', adv_col]).copy()
                            display_df['TotalSum'] = display_df['TotalSum'].apply(lambda x: f"{x:,.0f}")
                            st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("Выберите рекламодателей для анализа")
        else:
            st.info("Нет данных TotalSum.")
    else:
        st.warning("Нет Day-split данных с датами.")

# ─────────── TAB 2: Динамика (метрики × advertiser × banner_type) ───────────
with tab2:
    st.subheader("Динамика метрик × Advertiser × BannerType")

    if not df_day.empty and 'date' in df_day.columns:
        src = df_day
        engine_d = AnalysisEngine(src)
        
        # Настройки
        col_settings1, col_settings2 = st.columns(2)
        with col_settings1:
            period = st.selectbox("Период:", ["Месяц (M)", "Неделя (W)", "Квартал (Q)"], key="dyn_p")
        period_code = period.split("(")[1].strip(")")
        
        dyn = engine_d.dynamics(period_code, per_advertiser=True)

        if not dyn.empty:
            adv_col = next((c for c in ('advertiser', 'advertiser_id') if c in dyn.columns), None)
            
            if adv_col:
                # Выбор рекламодателей
                all_advs = sorted(dyn[adv_col].unique().tolist())
                with col_settings2:
                    selected_advs = st.multiselect(
                        "Рекламодатели:",
                        all_advs,
                        default=all_advs[:min(3, len(all_advs))],
                        key="tab2_advs"
                    )
                
                if selected_advs:
                    dyn_filtered = dyn[dyn[adv_col].isin(selected_advs)]
                    
                    # Выбор метрик
                    avail = [m for m in PERF_METRICS if m in dyn.columns and m != 'TotalSum']
                    sel_metrics = st.multiselect("Метрики:", avail, default=avail[:4], key="dyn_m")

                    if sel_metrics:
                        # Графики для каждого рекламодателя × метрика (по 2 в строку)
                        for adv in selected_advs:
                            st.markdown(f"### {adv}")
                            adv_data = dyn_filtered[dyn_filtered[adv_col] == adv]
                            
                            for i in range(0, len(sel_metrics), 2):
                                cols = st.columns(2)
                                for j, col in enumerate(cols):
                                    if i + j < len(sel_metrics):
                                        metric = sel_metrics[i + j]
                                        with col:
                                            import plotly.express as px
                                            fig = px.line(adv_data, x='period', y=metric, markers=True)
                                            
                                            # Расчёт изменения
                                            if len(adv_data) >= 2 and metric in adv_data.columns:
                                                first = adv_data[metric].iloc[0]
                                                last = adv_data[metric].iloc[-1]
                                                if first and first > 0:
                                                    change = ((last - first) / first * 100)
                                                    trend = "📈" if change > 5 else "📉" if change < -5 else "➡️"
                                                    title = f"{metric} {trend} {change:+.1f}%"
                                                else:
                                                    title = metric
                                            else:
                                                title = metric
                                            
                                            fig.update_layout(
                                                title=dict(text=title, font=dict(size=12)),
                                                showlegend=False,
                                                height=220,
                                                margin=dict(l=40, r=20, t=35, b=25),
                                                xaxis_title=None,
                                                yaxis_title=None,
                                                hovermode='x unified',
                                            )
                                            fig.update_traces(
                                                hovertemplate='%{y:,.3f}<extra></extra>',
                                                line=dict(width=2),
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Таблица сравнения с подсветкой лучших показателей
                        st.markdown("---")
                        st.markdown("### 📊 Сравнение показателей (средние значения)")
                        
                        # Агрегируем данные для сравнения
                        comparison_data = []
                        for adv in selected_advs:
                            adv_data = dyn_filtered[dyn_filtered[adv_col] == adv]
                            row = {adv_col: adv}
                            for metric in sel_metrics:
                                if metric in adv_data.columns:
                                    avg_val = adv_data[metric].mean()
                                    row[metric] = avg_val
                                    
                                    # Добавляем динамику
                                    if len(adv_data) >= 2:
                                        first = adv_data[metric].iloc[0]
                                        last = adv_data[metric].iloc[-1]
                                        if first and first > 0:
                                            change = ((last - first) / first * 100)
                                            trend = "📈" if change > 5 else "📉" if change < -5 else "➡️"
                                            row[f'{metric} динамика'] = f"{trend} {change:+.1f}%"
                                        else:
                                            row[f'{metric} динамика'] = "—"
                                    else:
                                        row[f'{metric} динамика'] = "—"
                            comparison_data.append(row)
                        
                        comp_df = pd.DataFrame(comparison_data)
                        
                        # Форматируем числовые колонки
                        comp_df_display = comp_df.copy()
                        for col in comp_df_display.columns:
                            if col != adv_col and 'динамика' not in col and pd.api.types.is_numeric_dtype(comp_df_display[col]):
                                comp_df_display[col] = comp_df_display[col].apply(lambda x: format_metric(x, col))
                        
                        st.dataframe(comp_df_display, use_container_width=True)
                        
                        # Детальная таблица
                        st.markdown("#### 📋 Детальные данные")
                        detail_df = dyn_filtered.drop(columns=['TotalSum'], errors='ignore').copy()
                        detail_df_formatted = format_dataframe(detail_df, exclude_cols=[adv_col, 'period'])
                        st.dataframe(detail_df_formatted, use_container_width=True)
                else:
                    st.info("Выберите рекламодателей")
    else:
        st.warning("Нет Day-split данных.")

    # BannerType breakdown
    if not df_bt.empty:
        st.markdown("---")
        st.markdown("### 📊 В разрезе BannerType")
        
        adv_col_bt = next((c for c in ('advertiser', 'advertiser_id') if c in df_bt.columns), None)
        if adv_col_bt:
            all_advs_bt = sorted(df_bt[adv_col_bt].unique().tolist())
            selected_advs_bt = st.multiselect(
                "Рекламодатели (BannerType):",
                all_advs_bt,
                default=all_advs_bt[:min(3, len(all_advs_bt))],
                key="tab2_bt_advs"
            )
            
            if selected_advs_bt:
                df_bt_filtered = df_bt[df_bt[adv_col_bt].isin(selected_advs_bt)]
                engine_bt = AnalysisEngine(df_bt_filtered)
                bt_data = engine_bt.media_split('banner_type', per_advertiser=True)
                
                if not bt_data.empty:
                    show = [c for c in [adv_col_bt, 'banner_type'] + PERF_METRICS
                            if c in bt_data.columns and c != 'TotalSum']
                    
                    # Форматируем данные
                    bt_display = format_dataframe(bt_data[show].sort_values(show[:2]), exclude_cols=[adv_col_bt, 'banner_type'])
                    st.dataframe(bt_display, use_container_width=True)

# ─────────── TAB 3: BannerSize ───────────
with tab3:
    st.subheader("BannerSize — анализ размеров баннеров")

    if not df_bs.empty and 'banner_size' in df_bs.columns:
        adv_col_bs = next((c for c in ('advertiser', 'advertiser_id') if c in df_bs.columns), None)
        
        # Настройки фильтрации
        col_f1, col_f2 = st.columns(2)
        
        if adv_col_bs:
            all_advs_bs = sorted(df_bs[adv_col_bs].unique().tolist())
            with col_f1:
                selected_advs_bs = st.multiselect(
                    "Рекламодатели:",
                    all_advs_bs,
                    default=all_advs_bs[:min(3, len(all_advs_bs))],
                    key="tab3_advs"
                )
        
        # Фильтруем по рекламодателям
        if adv_col_bs and selected_advs_bs:
            df_bs_filtered = df_bs[df_bs[adv_col_bs].isin(selected_advs_bs)]
        else:
            df_bs_filtered = df_bs
        
        # Получаем все размеры и сортируем по показам
        all_sizes = df_bs_filtered.groupby('banner_size')['impressions'].sum().sort_values(ascending=False)
        all_sizes_list = all_sizes.index.tolist()
        
        with col_f2:
            selected_sizes = st.multiselect(
                "Размеры баннеров (по показам ↓):",
                all_sizes_list,
                default=all_sizes_list[:min(8, len(all_sizes_list))],
                key="tab3_sizes"
            )
        
        if selected_sizes:
            df_bs_display = df_bs_filtered[df_bs_filtered['banner_size'].isin(selected_sizes)]
            
            # Агрегируем по размерам (для диаграммы)
            bs_agg = df_bs_display.groupby('banner_size').agg({
                'impressions': 'sum',
                'clicks': 'sum' if 'clicks' in df_bs_display.columns else lambda x: 0,
            }).reset_index()
            bs_agg = bs_agg.sort_values('impressions', ascending=False)
            
            # Диаграмма - отсортирована по показам
            import plotly.express as px
            fig = px.bar(
                bs_agg, 
                x='banner_size', 
                y='impressions',
                title="Показы по размерам баннеров",
                text='impressions'
            )
            fig.update_layout(
                showlegend=False,
                height=350,
                xaxis_title=None,
                yaxis_title="Impressions",
                xaxis={'categoryorder': 'total descending'}
            )
            fig.update_traces(
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='%{x}<br>Показы: %{y:,.0f}<extra></extra>'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Таблица с подсветкой лучших показателей
            st.markdown("### 📊 Детальная статистика")
            
            engine_bs = AnalysisEngine(df_bs_display)
            bs_all = engine_bs.banner_size_analysis(df_bs_display)
            
            if not bs_all.empty:
                show_cols = [c for c in [adv_col_bs, 'banner_size'] + PERF_METRICS
                             if c and c in bs_all.columns and c != 'TotalSum']
                
                # Сортируем по показам
                if 'impressions' in bs_all.columns:
                    bs_all = bs_all.sort_values('impressions', ascending=False)
                
                # Форматируем данные
                bs_display = format_dataframe(bs_all[show_cols], exclude_cols=[adv_col_bs, 'banner_size'])
                st.dataframe(bs_display, use_container_width=True)
                
                # Сравнение по рекламодателям
                if adv_col_bs and len(selected_advs_bs) > 1:
                    st.markdown("### 🔀 Сравнение рекламодателей по размерам")
                    
                    pivot = bs_all.pivot_table(
                        index='banner_size',
                        columns=adv_col_bs,
                        values=['impressions', 'ctr'] if 'ctr' in bs_all.columns else ['impressions'],
                        aggfunc='mean'
                    ).round(4)
                    
                    st.dataframe(pivot, use_container_width=True)
        else:
            st.info("Выберите размеры баннеров для анализа")
    else:
        st.warning("Нет BannerSize данных.")

# ─────────── TAB 4: Multi-Advertiser Comparison ───────────
with tab4:
    st.subheader("🔀 Сводное сравнение рекламодателей")

    # determine advertiser column
    adv_col_m = None
    for df_check in [df_day, df_bt, df_bs]:
        if not df_check.empty:
            for c in ('advertiser', 'advertiser_source', 'credential_source', 'advertiser_id'):
                if c in df_check.columns:
                    adv_col_m = c
                    break
        if adv_col_m:
            break

    if adv_col_m and not df_day.empty and df_day[adv_col_m].nunique() >= 1:
        all_advs_m = sorted(df_day[adv_col_m].unique().tolist())
        selected_advs_m = st.multiselect(
            "Выберите рекламодателей для сравнения:",
            all_advs_m,
            default=all_advs_m,
            key="tab4_advs"
        )
        
        if selected_advs_m:
            # === ОБЩАЯ СВОДКА ===
            st.markdown("### 📊 Общая сводка по рекламодателям")
            
            df_day_filtered = df_day[df_day[adv_col_m].isin(selected_advs_m)]
            
            summary_data = []
            for adv in selected_advs_m:
                adv_df = df_day_filtered[df_day_filtered[adv_col_m] == adv]
                row = {adv_col_m: adv}
                
                for metric in ['impressions', 'clicks', 'TotalSum']:
                    if metric in adv_df.columns:
                        row[metric] = adv_df[metric].sum()
                
                for metric in ['ctr', 'cpc', 'cpm', 'viewability', 'vtr', 'frequency']:
                    if metric in adv_df.columns:
                        row[metric] = adv_df[metric].mean()
                
                summary_data.append(row)
            
            summary_df = pd.DataFrame(summary_data)
            
            # Форматируем для отображения
            summary_display = summary_df.copy()
            for col in summary_display.columns:
                if col != adv_col_m and pd.api.types.is_numeric_dtype(summary_display[col]):
                    summary_display[col] = summary_display[col].apply(lambda x: format_metric(x, col))
            
            st.dataframe(summary_display, use_container_width=True)
            
            # === ИНСАЙТЫ ===
            st.markdown("### 💡 Ключевые инсайты")
            
            insights = []
            
            # Лидер по показам
            if 'impressions' in summary_df.columns:
                leader_imp = summary_df.loc[summary_df['impressions'].idxmax()]
                insights.append(f"📺 **Лидер по показам**: {leader_imp[adv_col_m]} ({leader_imp['impressions']:,.0f})")
            
            # Лидер по CTR
            if 'ctr' in summary_df.columns:
                leader_ctr = summary_df.loc[summary_df['ctr'].idxmax()]
                worst_ctr = summary_df.loc[summary_df['ctr'].idxmin()]
                insights.append(f"🎯 **Лучший CTR**: {leader_ctr[adv_col_m]} ({leader_ctr['ctr']:.3%})")
                if len(selected_advs_m) > 1:
                    insights.append(f"⚠️ **Худший CTR**: {worst_ctr[adv_col_m]} ({worst_ctr['ctr']:.3%})")
            
            # Лидер по расходам
            if 'TotalSum' in summary_df.columns:
                leader_spend = summary_df.loc[summary_df['TotalSum'].idxmax()]
                insights.append(f"💰 **Максимальный расход**: {leader_spend[adv_col_m]} ({leader_spend['TotalSum']:,.0f})")
            
            # Лучший CPC
            if 'cpc' in summary_df.columns:
                best_cpc = summary_df.loc[summary_df['cpc'].idxmin()]
                insights.append(f"💵 **Лучший CPC**: {best_cpc[adv_col_m]} ({best_cpc['cpc']:.2f})")
            
            # Viewability
            if 'viewability' in summary_df.columns:
                best_view = summary_df.loc[summary_df['viewability'].idxmax()]
                insights.append(f"👁️ **Лучшая viewability**: {best_view[adv_col_m]} ({best_view['viewability']:.1%})")
            
            for insight in insights:
                st.markdown(insight)
            
            # === ДИНАМИКА ===
            st.markdown("---")
            st.markdown("### 📈 Динамика показателей")
            
            engine_m = AnalysisEngine(df_day_filtered)
            dyn_m = engine_m.dynamics('M', per_advertiser=True)
            
            if not dyn_m.empty:
                dynamics_insights = []
                for adv in selected_advs_m:
                    adv_dyn = dyn_m[dyn_m[adv_col_m] == adv]
                    if len(adv_dyn) >= 2:
                        for metric in ['TotalSum', 'impressions', 'ctr']:
                            if metric in adv_dyn.columns:
                                first = adv_dyn[metric].iloc[0]
                                last = adv_dyn[metric].iloc[-1]
                                if first and first > 0:
                                    change = ((last - first) / first * 100)
                                    trend = "📈" if change > 5 else "📉" if change < -5 else "➡️"
                                    dynamics_insights.append({
                                        'Рекламодатель': adv,
                                        'Метрика': metric,
                                        'Изменение': f"{change:+.1f}%",
                                        'Тренд': trend
                                    })
                
                if dynamics_insights:
                    dyn_df = pd.DataFrame(dynamics_insights)
                    st.dataframe(dyn_df, use_container_width=True)
            
            # === BANNER TYPE ===
            if not df_bt.empty and adv_col_m in df_bt.columns:
                st.markdown("---")
                st.markdown("### 📊 По типам баннеров")
                
                df_bt_filtered = df_bt[df_bt[adv_col_m].isin(selected_advs_m)]
                
                if 'banner_type' in df_bt_filtered.columns:
                    bt_pivot = df_bt_filtered.pivot_table(
                        index='banner_type',
                        columns=adv_col_m,
                        values=['impressions', 'ctr'] if 'ctr' in df_bt_filtered.columns else ['impressions'],
                        aggfunc='sum' if 'impressions' else 'mean'
                    ).round(4)
                    
                    st.dataframe(bt_pivot, use_container_width=True)
            
            # === BANNER SIZE ===
            if not df_bs.empty and adv_col_m in df_bs.columns:
                st.markdown("---")
                st.markdown("### 📐 Топ размеры баннеров")
                
                df_bs_filtered = df_bs[df_bs[adv_col_m].isin(selected_advs_m)]
                
                # Топ-5 размеров по показам
                top_sizes = df_bs_filtered.groupby('banner_size')['impressions'].sum().nlargest(5).index.tolist()
                df_bs_top = df_bs_filtered[df_bs_filtered['banner_size'].isin(top_sizes)]
                
                bs_pivot = df_bs_top.pivot_table(
                    index='banner_size',
                    columns=adv_col_m,
                    values='impressions',
                    aggfunc='sum'
                )
                
                st.dataframe(
                    bs_pivot.style.background_gradient(cmap='Greens', axis=1),
                    use_container_width=True
                )
        else:
            st.info("Выберите рекламодателей для сравнения")
    else:
        st.info("Для сравнения нужны данные минимум от одного рекламодателя.")

# ─────────── TAB 5: AI / QBR ───────────
with tab5:
    st.subheader("🤖 AI Анализ данных (Groq LLM)")

    api_key = st.session_state.get('llm_key', config.GROQ_API_KEY or '')
    model = st.session_state.get('llm_model', config.GROQ_MODEL)

    if not api_key:
        st.warning("⚠️ Добавьте Groq API Key в sidebar → 🤖 Groq LLM")
        st.markdown("👉 [Получить бесплатный ключ](https://console.groq.com/keys)")
        st.stop()

    st.success(f"✅ Groq подключен | Модель: **{model}**")
    
    # Показываем какие данные загружены
    data_info = []
    if not df_day.empty:
        data_info.append(f"📊 Основные данные: {len(df_day)} строк, {len(df_day.columns)} колонок")
        data_info.append(f"   Колонки: {', '.join(df_day.columns[:10])}{'...' if len(df_day.columns) > 10 else ''}")
    if not df_bt.empty:
        data_info.append(f"📈 BannerType: {len(df_bt)} строк")
    if not df_bs.empty:
        data_info.append(f"📐 BannerSize: {len(df_bs)} строк")
    
    if data_info:
        st.markdown("**Загруженные данные:**")
        for info in data_info:
            st.markdown(info)
    
    analysis_type = st.selectbox("Тип анализа:", [
        "🔬 Универсальный анализ данных",
        "📊 Найти инсайты и закономерности",
        "📈 Анализ трендов и динамики",
        "💡 Рекомендации по оптимизации",
        "📝 Краткое резюме данных",
        "❓ Свой вопрос к данным",
    ])
    
    # Поле для своего вопроса
    custom_question = ""
    if analysis_type == "❓ Свой вопрос к данным":
        custom_question = st.text_area(
            "Ваш вопрос:",
            placeholder="Например: Какой рекламодатель показывает лучшую динамику? Где есть проблемы?"
        )

    if st.button("🚀 Запустить AI анализ", type="primary"):
        from ai_layer import LLMInsightGenerator
        llm = LLMInsightGenerator(api_key=api_key, model=model)

        with st.spinner("🤖 AI анализирует данные..."):
            try:
                # Подготавливаем данные для анализа
                data_summary = []
                
                if not df_day.empty:
                    data_summary.append("=== ОСНОВНЫЕ ДАННЫЕ ===")
                    data_summary.append(f"Размер: {len(df_day)} строк × {len(df_day.columns)} колонок")
                    data_summary.append(f"Колонки: {list(df_day.columns)}")
                    data_summary.append("\nСтатистика:")
                    data_summary.append(df_day.describe(include='all').to_string())
                    data_summary.append("\nПервые 20 строк:")
                    data_summary.append(df_day.head(20).to_string())
                    if len(df_day) > 20:
                        data_summary.append("\nПоследние 10 строк:")
                        data_summary.append(df_day.tail(10).to_string())
                
                if not df_bt.empty:
                    data_summary.append("\n=== ДАННЫЕ ПО ТИПАМ ===")
                    data_summary.append(df_bt.to_string())
                
                if not df_bs.empty:
                    data_summary.append("\n=== ДАННЫЕ ПО РАЗМЕРАМ ===")
                    data_summary.append(df_bs.head(30).to_string())
                
                data_text = "\n".join(data_summary)
                
                # Выбираем промпт в зависимости от типа анализа
                if analysis_type == "🔬 Универсальный анализ данных":
                    system_prompt = """Ты — эксперт по анализу данных. Проанализируй предоставленные данные и дай:

1. **Общая картина** — что это за данные, что они показывают
2. **Ключевые метрики** — главные числа и показатели
3. **Инсайты** — интересные закономерности, аномалии, тренды
4. **Сравнение** — если есть несколько сущностей (рекламодателей, периодов) — сравни их
5. **Выводы** — главные takeaways
6. **Рекомендации** — что можно улучшить

Пиши на русском. Будь конкретен, указывай цифры."""

                elif analysis_type == "📊 Найти инсайты и закономерности":
                    system_prompt = """Ты — аналитик данных. Найди в данных:

1. **Неочевидные закономерности** — что не видно на первый взгляд
2. **Аномалии** — выбросы, странные значения
3. **Корреляции** — что с чем связано
4. **Лидеры и аутсайдеры** — кто лучший, кто худший
5. **Точки роста** — где есть потенциал

Пиши на русском. Указывай конкретные цифры и проценты."""

                elif analysis_type == "📈 Анализ трендов и динамики":
                    system_prompt = """Ты — аналитик трендов. Проанализируй динамику данных:

1. **Общий тренд** — рост, падение, стабильность
2. **Сезонность** — есть ли циклы
3. **Точки перелома** — когда что-то изменилось
4. **Прогноз** — что будет дальше при текущих трендах
5. **Сравнение периодов** — как менялись показатели

Пиши на русском. Указывай даты и проценты изменений."""

                elif analysis_type == "💡 Рекомендации по оптимизации":
                    system_prompt = """Ты — консультант по оптимизации. На основе данных дай:

1. **Что работает хорошо** — на что опираться
2. **Что требует внимания** — проблемные зоны
3. **Быстрые победы** — что можно улучшить легко
4. **Стратегические изменения** — что менять в долгосрок
5. **Конкретные действия** — пошаговый план

Пиши на русском. Будь практичен и конкретен."""

                elif analysis_type == "📝 Краткое резюме данных":
                    system_prompt = """Дай краткое резюме данных в 5-7 пунктах:

- Что это за данные
- Ключевые цифры
- Главный вывод
- Одна рекомендация

Пиши кратко, на русском."""

                else:  # Свой вопрос
                    system_prompt = f"""Ответь на вопрос пользователя на основе данных.
                    
Вопрос: {custom_question}

Пиши на русском. Будь конкретен, ссылайся на данные."""

                result = llm._chat(system_prompt, data_text, max_tokens=4000)

                st.markdown("---")
                st.markdown(result)
                
                # Кнопка скачивания
                st.download_button(
                    "📥 Скачать отчёт",
                    result,
                    file_name="ai_analysis_report.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"Ошибка: {e}")

# Footer
st.markdown("---")
st.markdown("**DSP Analytics Platform** | Hybrid.ai DSP | QBR & Competitive Analysis")

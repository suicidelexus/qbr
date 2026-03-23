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

# — LLM settings —
st.sidebar.markdown("---")
st.sidebar.header("🤖 LLM (OpenAI)")
with st.sidebar.expander("Настройки LLM", expanded=False):
    llm_key = st.text_input("OpenAI API Key", type="password",
                            value=st.session_state.get('llm_key', config.OPENAI_API_KEY or ''))
    llm_model = st.selectbox("Модель", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                             index=0)
    if st.button("💾 Сохранить LLM"):
        st.session_state['llm_key'] = llm_key
        st.session_state['llm_model'] = llm_model
        st.success("✓")

# — Data loading —
st.sidebar.markdown("---")
st.sidebar.header("📥 Загрузка данных")
days = st.sidebar.slider("Период (дней):", 1, 90, 30)

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

            # spend line chart per advertiser
            if adv_col:
                fig = chart_gen.dynamics_line(dyn, metrics=['TotalSum'], color_by=adv_col)
                fig.update_layout(title="TotalSum по месяцам", yaxis_title="TotalSum")
                st.plotly_chart(fig, use_container_width=True)

            # table
            show = _available(dyn, [adv_col, 'period', 'TotalSum'])
            if show:
                st.dataframe(dyn[show].sort_values('period'), use_container_width=True)
        else:
            st.info("Нет данных TotalSum.")
    else:
        st.warning("Нет Day-split данных с датами.")

# ─────────── TAB 2: Динамика (всё кроме TotalSum, × advertiser × banner_type) ───────────
with tab2:
    st.subheader("Динамика метрик × Advertiser × BannerType")

    # prefer df_day (has dates); also use df_bt for banner_type info
    if not df_day.empty and 'date' in df_day.columns:
        # If df_bt is available, we use it for banner_type breakdown per month
        # Otherwise we just show day-level dynamics
        src = df_day
        has_bt = 'banner_type' in src.columns

        engine_d = AnalysisEngine(src)
        period = st.selectbox("Период:", ["Месяц (M)", "Неделя (W)", "Квартал (Q)"], key="dyn_p")
        period_code = period.split("(")[1].strip(")")

        dyn = engine_d.dynamics(period_code, per_advertiser=True)

        if not dyn.empty:
            # drop TotalSum from display
            avail = [m for m in PERF_METRICS if m in dyn.columns and m != 'TotalSum']
            sel = st.multiselect("Метрики:", avail, default=avail[:3], key="dyn_m")

            adv_col = next((c for c in ('advertiser', 'advertiser_id') if c in dyn.columns), None)

            if sel and adv_col:
                fig = chart_gen.dynamics_line(dyn, metrics=sel, color_by=adv_col)
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(dyn.drop(columns=['TotalSum'], errors='ignore'), use_container_width=True)
    else:
        st.warning("Нет Day-split данных.")

    # BannerType breakdown (from df_bt)
    if not df_bt.empty:
        st.markdown("---")
        st.markdown("### В разрезе BannerType")
        engine_bt = AnalysisEngine(df_bt)
        bt_data = engine_bt.media_split('banner_type', per_advertiser=True)
        if not bt_data.empty:
            show = [c for c in ['advertiser', 'banner_type'] + PERF_METRICS
                    if c in bt_data.columns and c != 'TotalSum']
            st.dataframe(bt_data[show].sort_values(show[:2]), use_container_width=True)

# ─────────── TAB 3: BannerSize (filtered) ───────────
with tab3:
    st.subheader("BannerSize — display")

    if not df_bs.empty and 'banner_size' in df_bs.columns:
        engine_bs = AnalysisEngine(df_bs)
        bs_all = engine_bs.banner_size_analysis(df_bs)

        if not bs_all.empty:
            adv_col_bs = next((c for c in ('advertiser', 'advertiser_id') if c in bs_all.columns), None)

            # filter advertiser
            if adv_col_bs:
                advs_list = ['Все'] + sorted(bs_all[adv_col_bs].unique().tolist())
                sel_adv = st.selectbox("Рекламодатель:", advs_list, key="bs_adv")
                if sel_adv != 'Все':
                    bs_all = bs_all[bs_all[adv_col_bs] == sel_adv]

            show_cols = [c for c in [adv_col_bs, 'banner_size'] + PERF_METRICS
                         if c and c in bs_all.columns and c != 'TotalSum']

            # PRIMARY sizes
            primary = bs_all[bs_all['banner_size'].isin(config.BANNER_SIZE_PRIMARY)]
            if not primary.empty:
                st.markdown("#### Основные размеры")
                fig = chart_gen.banner_size_chart(primary, adv_col=adv_col_bs)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(primary[show_cols].sort_values('impressions', ascending=False)
                             if 'impressions' in primary.columns else primary[show_cols],
                             use_container_width=True)

            # SECONDARY sizes (expander)
            secondary = bs_all[bs_all['banner_size'].isin(config.BANNER_SIZE_SECONDARY)]
            if not secondary.empty:
                with st.expander("📂 Дополнительные размеры", expanded=False):
                    fig2 = chart_gen.banner_size_chart(secondary, adv_col=adv_col_bs)
                    st.plotly_chart(fig2, use_container_width=True)
                    st.dataframe(secondary[show_cols].sort_values('impressions', ascending=False)
                                 if 'impressions' in secondary.columns else secondary[show_cols],
                                 use_container_width=True)
        else:
            st.info("Нет данных BannerSize.")
    else:
        st.warning("Нет BannerSize данных.")

# ─────────── TAB 4: Multi-Advertiser Comparison ───────────
with tab4:
    st.subheader("🔀 Сравнение рекламодателей")

    # determine advertiser column across all dfs
    adv_col_m = None
    for df_check in [df_day, df_bt, df_bs]:
        for c in ('advertiser', 'advertiser_source', 'credential_source'):
            if c in df_check.columns:
                adv_col_m = c
                break
        if adv_col_m:
            break

    if adv_col_m and not df_day.empty and df_day[adv_col_m].nunique() >= 2:
        from multi_advertiser import MultiAdvertiserManager
        mgr = MultiAdvertiserManager()

        # Day comparison
        st.markdown("### Day split — сравнение")
        summary_day = mgr.get_comparison_summary(df_day)
        if not summary_day.empty:
            show = _available(summary_day, [adv_col_m] + PERF_METRICS + ['TotalSum'])
            st.dataframe(summary_day[show], use_container_width=True)

        # BannerType comparison
        if not df_bt.empty:
            st.markdown("### BannerType — сравнение")
            bt_comp = mgr.compare_by_dimension(df_bt, 'banner_type')
            if not bt_comp.empty:
                show_bt = _available(bt_comp, [adv_col_m, 'banner_type'] + PERF_METRICS)
                st.dataframe(bt_comp[show_bt], use_container_width=True)

        # BannerSize comparison
        if not df_bs.empty:
            st.markdown("### BannerSize — сравнение")
            bs_comp = mgr.compare_by_dimension(df_bs, 'banner_size')
            if not bs_comp.empty:
                # filter to known sizes
                bs_comp = bs_comp[bs_comp['banner_size'].isin(config.BANNER_SIZE_ALL)]
                show_bs = _available(bs_comp, [adv_col_m, 'banner_size'] + PERF_METRICS)
                st.dataframe(bs_comp[show_bs], use_container_width=True)
    else:
        st.info("Для сравнения нужны данные минимум 2 рекламодателей. "
                "Добавьте несколько credentials или загрузите данные agency-аккаунта.")

# ─────────── TAB 5: AI / QBR ───────────
with tab5:
    st.subheader("🤖 AI Insights & QBR")

    api_key = st.session_state.get('llm_key', config.OPENAI_API_KEY or '')
    model = st.session_state.get('llm_model', config.OPENAI_MODEL)

    if not api_key:
        st.warning("⚠️ Настройте OpenAI API Key в sidebar для LLM-инсайтов. "
                   "Без ключа доступен только rule-based анализ.")

    col_a, col_b = st.columns(2)

    # — Rule-based (always available) —
    with col_a:
        st.markdown("### 📋 Rule-based анализ")
        if st.button("Сгенерировать"):
            from ai_layer import InsightGenerator
            ai_df = df_day if not df_day.empty else df_bt
            ig = InsightGenerator(ai_df)
            res = ig.generate_full_analysis()
            st.text(res['tldr'])
            for ins in res['advertisers']['insights'] + res['dynamics']['insights']:
                st.markdown(f"- {ins}")
            if res['recommendations']:
                st.markdown("**Рекомендации:**")
                for r in res['recommendations']:
                    st.markdown(f"- {r}")

    # — LLM-powered —
    with col_b:
        st.markdown("### 🧠 LLM Insights")
        if not api_key:
            st.info("Добавьте OpenAI API Key")
        else:
            analysis_type = st.selectbox("Тип анализа:", [
                "Advertisers (расходы)",
                "Динамика (метрики)",
                "BannerSize",
                "Конкурентный анализ",
                "📄 QBR (полный отчёт)",
            ], key="llm_type")

            if st.button("🚀 Запустить LLM анализ"):
                from ai_layer import LLMInsightGenerator
                llm = LLMInsightGenerator(api_key=api_key, model=model)

                with st.spinner("LLM анализирует данные..."):
                    try:
                        if analysis_type.startswith("Advertisers"):
                            engine_a = AnalysisEngine(df_day)
                            dyn_a = engine_a.dynamics('M', per_advertiser=True)
                            result = llm.analyze_advertisers(dyn_a)
                        elif analysis_type.startswith("Динамика"):
                            src = df_bt if not df_bt.empty else df_day
                            result = llm.analyze_dynamics(src)
                        elif analysis_type.startswith("BannerSize"):
                            result = llm.analyze_banner_sizes(df_bs)
                        elif analysis_type.startswith("Конкурент"):
                            result = llm.generate_competitive_summary({
                                'Day': df_day, 'BannerType': df_bt, 'BannerSize': df_bs,
                            })
                        else:  # QBR
                            result = llm.generate_qbr({
                                'Day': df_day, 'BannerType': df_bt, 'BannerSize': df_bs,
                            })

                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Ошибка LLM: {e}")

# Footer
st.markdown("---")
st.markdown("**DSP Analytics Platform** | Hybrid.ai DSP | QBR & Competitive Analysis")

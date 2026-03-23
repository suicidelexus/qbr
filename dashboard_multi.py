"""
Multi-Advertiser Dashboard
Streamlit интерфейс для работы с несколькими рекламодателями
"""
import streamlit as st
import pandas as pd
from multi_advertiser import MultiAdvertiserManager
from analytics_agent import AnalyticsAgent
from visualization import ChartGenerator
from automation_generator import AutomationGenerator
import plotly.graph_objects as go


# Настройка страницы
st.set_page_config(
    page_title="Multi-Advertiser Analytics",
    page_icon="👥",
    layout="wide"
)

# Заголовок
st.title("👥 Multi-Advertiser DSP Analytics")
st.markdown("Сравнительный анализ нескольких рекламодателей")

# Инициализация session state
if 'advertisers' not in st.session_state:
    st.session_state['advertisers'] = []
if 'multi_df' not in st.session_state:
    st.session_state['multi_df'] = None

# Sidebar - управление advertisers
st.sidebar.header("👥 Управление Advertisers")

with st.sidebar.expander("➕ Добавить Advertiser", expanded=len(st.session_state['advertisers']) == 0):
    with st.form("add_advertiser"):
        adv_name = st.text_input(
            "Название *",
            placeholder="Advertiser A",
            help="Название для идентификации"
        )
        
        adv_client_id = st.text_input(
            "Client ID *",
            placeholder="Ваш Client ID",
            help="Client ID (обязательно)"
        )
        
        adv_secret_key = st.text_input(
            "Secret Key *",
            type="password",
            placeholder="Ваш Secret Key",
            help="Secret Key для аутентификации (обязательно)"
        )
        
        submitted = st.form_submit_button("➕ Добавить")
        
        if submitted:
            if not adv_name or not adv_client_id or not adv_secret_key:
                st.error("❌ Заполните все обязательные поля")
            elif any(a['advertiser'] == adv_name for a in st.session_state['advertisers']):
                st.warning(f"⚠️ {adv_name} уже добавлен")
            else:
                st.session_state['advertisers'].append({
                    'advertiser': adv_name,
                    'client_id': adv_client_id,
                    'secret_key': adv_secret_key,
                })
                st.success(f"✓ Добавлен: {adv_name}")
                st.rerun()

# Список advertisers
if st.session_state['advertisers']:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Добавлено: {len(st.session_state['advertisers'])}**")
    
    for i, adv in enumerate(st.session_state['advertisers']):
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.text(f"✓ {adv['advertiser']}")
        with col2:
            if st.button("🗑️", key=f"del_{i}", help="Удалить"):
                st.session_state['advertisers'].pop(i)
                st.rerun()
    
    # Кнопки управления
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🧪 Тест всех", key="test_all_multi"):
            from data_layer import DSPClient
            has_401 = False
            for adv in st.session_state['advertisers']:
                try:
                    client = DSPClient(
                        client_id=adv.get('client_id'),
                        secret_key=adv.get('secret_key')
                    )
                    client.test_connection()
                    st.success(f"✓ {adv['advertiser']}")
                except RuntimeError as e:
                    err = str(e)
                    st.error(f"✗ {adv['advertiser']}: {err}")
                    if "401" in err:
                        has_401 = True
                except Exception as e:
                    st.error(f"✗ {adv['advertiser']}: {e}")
            if has_401:
                st.warning(
                    "**HTTP 401 — API отклоняет credentials.**\n\n"
                    "Возможные причины:\n"
                    "- Неверный Client ID или Secret Key\n"
                    "- API-доступ не активирован в кабинете Hybrid.ai\n\n"
                    "👇 Используйте **«🎲 Сгенерировать демо данные»** для работы без API"
                )
                except Exception as e:
                    st.error(f"✗ {adv['advertiser']}: {str(e)[:30]}")
    
    with col2:
        if st.button("🗑️ Очистить", key="clear_multi"):
            st.session_state['advertisers'] = []
            st.session_state['multi_df'] = None
            st.rerun()

else:
    st.sidebar.info("ℹ️ Добавьте хотя бы 2 advertisers для сравнения")

# Загрузка данных
st.sidebar.markdown("---")
st.sidebar.header("📥 Загрузка данных")

# ── Демо-режим (работает без API) ──────────────────────────
st.sidebar.markdown("**🧪 Без API:**")
if st.sidebar.button("🎲 Сгенерировать демо данные", use_container_width=True):
    import numpy as np
    from datetime import datetime, timedelta

    adv_names = [a['advertiser'] for a in st.session_state['advertisers']] or ['Advertiser A', 'Advertiser B', 'Advertiser C']
    products = ['Product 1', 'Product 2', 'Product 3']
    formats = ['video', 'banner', 'native']
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')

    rows = []
    for date in dates:
        for adv in adv_names:
            for product in products:
                for fmt in formats:
                    imp = np.random.randint(10_000, 100_000)
                    clk = int(imp * np.random.uniform(0.001, 0.006))
                    spend = imp * np.random.uniform(1, 5) / 1000
                    rows.append({
                        'date': date,
                        'advertiser_source': adv,
                        'advertiser': adv,
                        'product': product,
                        'format': fmt,
                        'impressions': imp,
                        'clicks': clk,
                        'TotalSum': spend,
                        'viewability': np.random.uniform(0.55, 0.95),
                        'frequency': np.random.uniform(1, 6),
                        'vtr': np.random.uniform(0.15, 0.45) if fmt == 'video' else 0.0,
                    })

    demo_df = pd.DataFrame(rows)
    demo_df['ctr'] = demo_df['clicks'] / demo_df['impressions']
    demo_df['cpm'] = demo_df['TotalSum'] / demo_df['impressions'] * 1000
    st.session_state['multi_df'] = demo_df
    st.sidebar.success(f"✅ Демо: {len(demo_df)} строк, {len(adv_names)} advertisers")
    st.rerun()

st.sidebar.markdown("**🌐 Из API:**")
if st.session_state['advertisers']:
    # Настройки периода
    period_type = st.sidebar.selectbox("Период:", ["Последние N дней", "Конкретный период"])

    if period_type == "Последние N дней":
        days = st.sidebar.slider("Дней:", 1, 90, 30)

        if st.sidebar.button("📥 Загрузить из API", use_container_width=True):
            with st.spinner("Загрузка данных от всех advertisers..."):
                try:
                    manager = MultiAdvertiserManager(credentials=st.session_state['advertisers'])

                    from datetime import datetime, timedelta
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=days)

                    df = manager.load_data(
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat(),
                        parallel=True
                    )

                    if not df.empty:
                        st.session_state['multi_df'] = df
                        st.success(f"✅ Загружено {len(df)} строк от {df['advertiser_source'].nunique()} advertisers")
                    else:
                        st.error("❌ Нет данных — используйте «🎲 Сгенерировать демо данные» или проверьте credentials через «🧪 Тест всех»")

                except Exception as e:
                    st.error(f"❌ {e}")

    else:  # Конкретный период
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("От:", value=pd.Timestamp.now() - pd.Timedelta(days=30))
        with col2:
            end_date = st.date_input("До:", value=pd.Timestamp.now())

        if st.sidebar.button("📥 Загрузить из API", use_container_width=True):
            with st.spinner("Загрузка..."):
                try:
                    manager = MultiAdvertiserManager(credentials=st.session_state['advertisers'])

                    df = manager.load_data(
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        parallel=True
                    )

                    if not df.empty:
                        st.session_state['multi_df'] = df
                        st.success(f"✅ Загружено {len(df)} строк")
                    else:
                        st.error("❌ Нет данных — используйте «🎲 Сгенерировать демо данные»")

                except Exception as e:
                    st.error(f"❌ {e}")
else:
    st.sidebar.info("☝️ Добавьте advertisers чтобы загрузить данные из API")

# Основной контент
if st.session_state['multi_df'] is not None and not st.session_state['multi_df'].empty:
    df = st.session_state['multi_df']
    
    # Валидация данных
    manager = MultiAdvertiserManager()
    validation = manager.validate_data_compatibility(df)
    
    # Основные метрики
    st.header("📈 Сводка по всем Advertisers")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Advertisers", validation['advertisers_count'])
    
    with col2:
        total_impressions = df['impressions'].sum()
        st.metric("Impressions", f"{total_impressions:,.0f}")
    
    with col3:
        avg_ctr = df['ctr'].mean()
        st.metric("Средний CTR", f"{avg_ctr:.3%}")
    
    with col4:
        total_spend = df['TotalSum'].sum()
        st.metric("Общий бюджет", f"{total_spend:,.0f}")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Сравнение Advertisers",
        "Кросс-анализ",
        "AI-Агент",
        "Кастомные запросы",
        "Экспорт & Автоматизация"
    ])
    
    with tab1:
        st.subheader("📊 Сравнение Advertisers")
        
        summary = manager.get_comparison_summary(df)
        
        if not summary.empty:
            # График сравнения
            chart_gen = ChartGenerator()
            fig = chart_gen.advertiser_comparison(summary)
            st.plotly_chart(fig, use_container_width=True)
            
            # Таблица
            st.markdown("### Детальная таблица")
            display_cols = [col for col in ['advertiser_source', 'impressions', 'clicks', 'ctr', 
                                            'TotalSum', 'cpm', 'viewability'] 
                           if col in summary.columns]
            st.dataframe(
                summary[display_cols].sort_values('ctr', ascending=False),
                use_container_width=True
            )
            
            # Инсайты
            st.markdown("### 💡 Ключевые инсайты")
            best = summary.nlargest(1, 'ctr').iloc[0]
            worst = summary.nsmallest(1, 'ctr').iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"🏆 Лидер по CTR: **{best['advertiser_source']}** ({best['ctr']:.3%})")
            with col2:
                st.warning(f"⚠️ Требует внимания: **{worst['advertiser_source']}** ({worst['ctr']:.3%})")
    
    with tab2:
        st.subheader("🔀 Кросс-анализ")
        
        # Выбор dimension для сравнения
        available_dims = [col for col in ['product', 'format', 'campaign'] if col in df.columns]
        
        if available_dims:
            dimension = st.selectbox("Сравнить по:", available_dims)
            
            comparison = manager.compare_by_dimension(df, dimension)
            
            if not comparison.empty:
                # Pivot таблица
                st.markdown(f"### Advertisers × {dimension}")
                
                pivot = comparison.pivot_table(
                    index='advertiser_source',
                    columns=dimension,
                    values='ctr',
                    aggfunc='mean'
                )
                
                st.dataframe(pivot.style.background_gradient(cmap='RdYlGn', axis=None), use_container_width=True)
                
                # Лучшие комбинации
                st.markdown("### 🏆 Топ-10 комбинаций")
                top = manager.find_best_performers(df, metric='ctr', dimension=dimension, top_n=10)
                st.dataframe(top, use_container_width=True)
        else:
            st.info("ℹ️ Недостаточно dimensions для кросс-анализа")
    
    with tab3:
        st.subheader("🤖 AI-Агент")
        
        if st.button("🚀 Запустить автоматический анализ", key="auto_analyze"):
            with st.spinner("AI анализирует данные..."):
                agent = AnalyticsAgent(df)
                analysis = agent.auto_analyze()
                
                # Приоритетные действия
                if analysis.get('priority_actions'):
                    st.markdown("### 🎯 Приоритетные действия")
                    for action in analysis['priority_actions']:
                        st.warning(f"⚠️ {action}")
                
                # Рекомендации для deep dive
                if analysis.get('deep_dive_suggestions'):
                    st.markdown("### 🔍 Рекомендуемые deep dive")
                    for suggestion in analysis['deep_dive_suggestions']:
                        priority_color = {
                            'HIGH': '🔴',
                            'MEDIUM': '🟡',
                            'LOW': '🟢'
                        }
                        icon = priority_color.get(suggestion['priority'], '⚪')
                        
                        with st.expander(f"{icon} {suggestion['suggestion']}"):
                            st.markdown(f"**Причина:** {suggestion['reason']}")
                            st.markdown(f"**Действие:** `{suggestion['action']}`")
                
                # Возможности оптимизации
                if analysis.get('opportunities'):
                    st.markdown("### 💰 Возможности оптимизации")
                    for opp in analysis['opportunities']:
                        impact_color = {
                            'HIGH': '🔴',
                            'MEDIUM': '🟡',
                            'LOW': '🟢'
                        }
                        icon = impact_color.get(opp['impact'], '⚪')
                        
                        st.info(f"{icon} **{opp['description']}**\n\n"
                               f"Действие: {opp['action']}\n\n"
                               f"Потенциал: {opp.get('potential_value', 'N/A')}")
                
                # Дополнительные вопросы
                if analysis.get('additional_questions'):
                    st.markdown("### ❓ Дополнительные вопросы для изучения")
                    for q in analysis['additional_questions'][:5]:
                        st.markdown(f"- {q}")
    
    with tab4:
        st.subheader("💬 Кастомные запросы")
        st.markdown("Задайте вопрос естественным языком")
        
        query = st.text_input(
            "Ваш вопрос:",
            placeholder="Например: сравни только video, покажи продукты с высоким CTR",
            help="AI попытается интерпретировать ваш запрос"
        )
        
        if st.button("🔍 Выполнить запрос") and query:
            with st.spinner("Обработка запроса..."):
                agent = AnalyticsAgent(df)
                result = agent.answer_custom_query(query)
                
                if 'error' in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✓ Запрос обработан")
                    
                    if result.get('type') == 'filter' and 'data' in result:
                        st.markdown(f"**Найдено:** {result['count']} строк")
                        st.dataframe(result['data'].head(50), use_container_width=True)
                    
                    elif result.get('type') == 'comparison' and 'results' in result:
                        for dim, data in result['results'].items():
                            st.markdown(f"### {dim}")
                            st.dataframe(data, use_container_width=True)
                    
                    elif result.get('type') == 'ranking' and 'top' in result:
                        st.markdown(f"### Топ по {result['metric']}")
                        st.dataframe(result['top'], use_container_width=True)
        
        # Примеры запросов
        with st.expander("💡 Примеры запросов"):
            st.markdown("""
            - `сравни только video`
            - `покажи продукты с высоким CTR`
            - `топ кампаний по конверсиям`
            - `сравни все форматы`
            - `найди проблемные кампании`
            """)
    
    with tab5:
        st.subheader("🔧 Экспорт и Автоматизация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Экспорт в Google")
            
            if st.button("📄 Экспорт в Google Sheets"):
                st.info("🚧 В разработке - см. google_export.py")
            
            if st.button("📽️ Экспорт в Google Slides"):
                st.info("🚧 В разработке - см. google_export.py")
        
        with col2:
            st.markdown("### ⚙️ Генератор автоматизации")
            
            schedule_type = st.selectbox(
                "Расписание:",
                ["daily", "weekly", "monthly", "hourly"]
            )
            
            if st.button("🤖 Сгенерировать код автоматизации"):
                with st.spinner("Генерация..."):
                    try:
                        gen = AutomationGenerator()
                        
                        # Генерируем скрипт
                        script = gen.generate_scheduler_script(
                            credentials=st.session_state['advertisers'],
                            schedule_type=schedule_type
                        )
                        
                        # Показываем код
                        st.markdown("### ✅ Код сгенерирован!")
                        
                        st.download_button(
                            label="📥 Скачать automation_script.py",
                            data=script,
                            file_name="automation_script.py",
                            mime="text/x-python"
                        )
                        
                        # Cron config
                        cron = gen.generate_cron_config(schedule_type)
                        st.download_button(
                            label="📥 Скачать cron_config.txt",
                            data=cron,
                            file_name="cron_config.txt",
                            mime="text/plain"
                        )
                        
                        st.success("✓ Файлы готовы к скачиванию")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")

else:
    st.info("👈 Добавьте advertisers в боковой панели")
    
    st.markdown("""
    ### 📋 Инструкции:
    
    1. **Добавьте advertisers** в боковой панели
       - Минимум 2 для сравнения
       - Введите название и API Key для каждого
    
    2. **Загрузите данные**
       - Выберите период
       - Нажмите "Загрузить данные"
       - Данные загрузятся параллельно от всех advertisers
    
    3. **Анализируйте**
       - **Сравнение Advertisers** - кто эффективнее
       - **Кросс-анализ** - advertiser × product/format
       - **AI-Агент** - автоматические рекомендации
       - **Кастомные запросы** - задавайте вопросы естественным языком
       - **Автоматизация** - генерация кода для регулярных отчетов
    
    ### 🎯 Возможности:
    
    - Параллельная загрузка данных
    - Автоматическая нормализация и валидация
    - Кросс-анализ по любым dimensions
    - AI-агент с активным анализом
    - Обработка естественных запросов
    - Генерация кода автоматизации
    - Экспорт в Google Slides/Sheets
    """)

# Footer
st.markdown("---")
st.markdown("**Multi-Advertiser DSP Analytics Platform** | Powered by AI")


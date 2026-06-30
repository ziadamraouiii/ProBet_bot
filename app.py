"""
تطبيق Streamlit الاحترافي لتحليل وتنبؤ نتائج كرة القدم
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

# إضافة المسار
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.data_fetcher import FootballDataFetcher
from src.analysis.advanced_analyzer import AdvancedFootballAnalyzer
from src.models.prediction_models import FootballPredictionModels

# ═══════════════════════════════════════════════════════
# إعدادات الصفحة
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="⚽ محلل المباريات الذكي",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════
# CSS مخصص
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    * { font-family: 'Tajawal', sans-serif; direction: rtl; }
    
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6, #1e3a8a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid #334155;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #3b82f6;
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    .prediction-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 20px;
        padding: 2rem;
        border: 2px solid #3b82f6;
        margin: 1rem 0;
    }
    
    .team-name {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    .vs-text {
        font-size: 2rem;
        font-weight: 900;
        color: #3b82f6;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: #94a3b8;
    }
    
    .stTabs [aria-selected="true"] {
        background: #3b82f6 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# تهيئة الجلسة
# ═══════════════════════════════════════════════════════
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None
    st.session_state.analyzer = None
    st.session_state.models = None
    st.session_state.training_results = None

# ═══════════════════════════════════════════════════════
# الشريط الجانبي
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ الإعدادات")
    st.markdown("---")
    st.markdown("### 📥 تحميل البيانات")
    data_source = st.radio("مصدر البيانات:", ["بيانات تجريبية", "رفع ملف CSV"], index=0)
    if data_source == "رفع ملف CSV":
        uploaded_file = st.file_uploader("اختر ملف CSV", type=['csv'])
    st.markdown("---")
    st.markdown("### ℹ️ معلومات")
    st.info("🏆 **50+ دوري عالمي**\n🤖 **3 نماذج ML**\n📊 **8 عوامل تحليلية**\n⚡ **تنبؤ فوري**")
    st.markdown("---")
    st.caption("© 2026 محلل المباريات الذكي")

# ═══════════════════════════════════════════════════════
# الرأس
# ═══════════════════════════════════════════════════════
st.markdown('<div class="main-header">⚽ محلل المباريات الذكي</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">نظام تنبؤ متقدم باستخدام الذكاء الاصطناعي وتحليل البيانات</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# تحميل البيانات
# ═══════════════════════════════════════════════════════
if not st.session_state.data_loaded:
    with st.spinner("🔄 جاري تحميل وتحليل البيانات..."):
        fetcher = FootballDataFetcher()
        if data_source == "بيانات تجريبية":
            df = fetcher.generate_sample_data(n_matches=5000)
        else:
            if 'uploaded_file' in locals() and uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
            else:
                df = fetcher.generate_sample_data(n_matches=5000)
        
        st.session_state.df = df
        st.session_state.analyzer = AdvancedFootballAnalyzer(df)
        st.session_state.models = FootballPredictionModels()
        
        X = st.session_state.models.prepare_features(df, st.session_state.analyzer)
        y = st.session_state.models.create_target(df)
        results = st.session_state.models.train(X, y)
        st.session_state.training_results = results
        st.session_state.data_loaded = True
        st.success(f"✅ تم تحميل {len(df)} مباراة و {len(X.columns)} ميزة!")

# ═══════════════════════════════════════════════════════
# علامات التبويب الرئيسية
# ═══════════════════════════════════════════════════════
tabs = st.tabs(["🔮 التنبؤ بالمباريات", "📊 لوحة التحليلات", "🤖 أداء النماذج", "📋 تقرير الميزات", "📚 الدليل"])

# ═══════════════════════════════════════════════════════
# تبويب 1: التنبؤ
# ═══════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("## 🔮 التنبؤ بنتيجة المباراة")
    
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 فريق أصحاب الأرض:", sorted(st.session_state.df['home_team'].unique()), index=0)
    with col2:
        away_team = st.selectbox("✈️ فريق الضيف:", sorted([t for t in st.session_state.df['away_team'].unique() if t != home_team]), index=0)
    
    if st.button("🔮 تنبأ بالنتيجة", type="primary", use_container_width=True):
        with st.spinner("🧠 جاري التحليل..."):
            factors = st.session_state.analyzer.get_all_factors(home_team, away_team)
            
            single_match = pd.DataFrame([{
                'home_team': home_team, 'away_team': away_team,
                'home_goals': 0, 'away_goals': 0,
                'date': pd.Timestamp.now(), 'league': 'Unknown', 'season': '2024-25'
            }])
            
            X_pred = st.session_state.models.prepare_features(single_match, st.session_state.analyzer)
            prediction = st.session_state.models.predict(X_pred)
            
            st.markdown("---")
            
            # صندوق التنبؤ
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.markdown(f"<h2 style='text-align: center; color: #3b82f6;'>{home_team}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #94a3b8;'>🏠 أصحاب الأرض</p>", unsafe_allow_html=True)
            with c2:
                st.markdown("<h1 style='text-align: center; color: #f59e0b;'>VS</h1>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<h2 style='text-align: center; color: #ef4444;'>{away_team}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #94a3b8;'>✈️ ضيف</p>", unsafe_allow_html=True)
            
            # الاحتمالات
            st.markdown("### 📊 احتمالات النتيجة")
            probs = prediction['probabilities']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dc2626, #991b1b); border-radius: 15px; padding: 1.5rem; text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs['away_win']}%</div>
                    <div style="color: #fecaca; margin-top: 0.5rem; font-size: 1.1rem;">فوز {away_team}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ca8a04, #854d0e); border-radius: 15px; padding: 1.5rem; text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs['draw']}%</div>
                    <div style="color: #fef08a; margin-top: 0.5rem; font-size: 1.1rem;">تعادل</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #16a34a, #166534); border-radius: 15px; padding: 1.5rem; text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs['home_win']}%</div>
                    <div style="color: #bbf7d0; margin-top: 0.5rem; font-size: 1.1rem;">فوز {home_team}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # التنبؤ النهائي
            pred_class = prediction['ensemble_class']
            pred_label = prediction['ensemble_prediction']
            confidence = prediction['confidence']
            
            if pred_class == 'home_win':
                color, emoji = '#16a34a', '🏆'
            elif pred_class == 'draw':
                color, emoji = '#ca8a04', '🤝'
            else:
                color, emoji = '#dc2626', '✈️'
            
            st.markdown(f"""
            <div style="background: {color}; border-radius: 15px; padding: 1.5rem; text-align: center; margin-top: 1rem;">
                <div style="font-size: 1.8rem; font-weight: 900; color: white;">{emoji} التنبؤ: {pred_label}</div>
                <div style="color: rgba(255,255,255,0.9); margin-top: 0.5rem; font-size: 1.2rem;">ثقة النموذج: {confidence}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            # العوامل التحليلية
            st.markdown("---")
            st.markdown("### 📈 العوامل التحليلية (8 عوامل)")
            
            factor_data = {
                'العامل': [
                    '📊 شكل الفريق (آخر 5)',
                    '⚽ القوة الهجومية',
                    '🛡️ القوة الدفاعية',
                    '🏟️ ميزة الملعب',
                    '🔄 تاريخ المواجهات',
                    '📋 الانضباط',
                    '🎯 كفاءة التسديد',
                    '📈 زخم الأداء'
                ],
                f'{home_team}': [
                    f"{factors['home_form']:.2f}",
                    f"{factors['home_offense']:.2f}",
                    f"{factors['home_defense']:.2f}",
                    f"{factors['home_advantage']:.2f}",
                    f"{factors['h2h_home']:.2f}",
                    f"{factors['home_discipline']:.2f}",
                    f"{factors['home_efficiency']:.2f}",
                    f"{factors['home_momentum']:.2f}"
                ],
                f'{away_team}': [
                    f"{factors['away_form']:.2f}",
                    f"{factors['away_offense']:.2f}",
                    f"{factors['away_defense']:.2f}",
                    f"{factors['away_advantage']:.2f}",
                    f"{1 - factors['h2h_home'] - factors['h2h_draw']:.2f}",
                    f"{factors['away_discipline']:.2f}",
                    f"{factors['away_efficiency']:.2f}",
                    f"{factors['away_momentum']:.2f}"
                ]
            }
            factor_df = pd.DataFrame(factor_data)
            st.dataframe(factor_df, use_container_width=True, hide_index=True)
            
            # مقارنة النماذج
            st.markdown("---")
            st.markdown("### 🤖 مقارنة النماذج")
            models_comp = prediction['individual_models']
            model_comparison_data = []
            for model_name, model_data in models_comp.items():
                model_comparison_data.append({
                    'النموذج': model_name.replace('_', ' ').title(),
                    'التنبؤ': model_data['prediction'],
                    'فوز ضيف': f"{model_data['probabilities']['away_win']:.1f}%",
                    'تعادل': f"{model_data['probabilities']['draw']:.1f}%",
                    'فوز أصحاب الأرض': f"{model_data['probabilities']['home_win']:.1f}%"
                })
            comp_df = pd.DataFrame(model_comparison_data)
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════
# تبويب 2: لوحة التحليلات
# ═══════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("## 📊 لوحة التحليلات الشاملة")
    df = st.session_state.df
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df):,}</div><div class="metric-label">إجمالي المباريات</div></div>', unsafe_allow_html=True)
    with col2:
        avg_goals = (df['home_goals'].sum() + df['away_goals'].sum()) / len(df)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_goals:.2f}</div><div class="metric-label">متوسط الأهداف/مباراة</div></div>', unsafe_allow_html=True)
    with col3:
        home_win_pct = ((df['home_goals'] > df['away_goals']).sum() / len(df)) * 100
        st.markdown(f'<div class="metric-card"><div class="metric-value">{home_win_pct:.1f}%</div><div class="metric-label">نسبة فوز أصحاب الأرض</div></div>', unsafe_allow_html=True)
    with col4:
        draw_pct = ((df['home_goals'] == df['away_goals']).sum() / len(df)) * 100
        st.markdown(f'<div class="metric-card"><div class="metric-value">{draw_pct:.1f}%</div><div class="metric-label">نسبة التعادل</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 توزيع نتائج المباريات")
        results_dist = pd.DataFrame({
            'النتيجة': ['فوز أصحاب الأرض', 'تعادل', 'فوز الضيف'],
            'العدد': [
                (df['home_goals'] > df['away_goals']).sum(),
                (df['home_goals'] == df['away_goals']).sum(),
                (df['home_goals'] < df['away_goals']).sum()
            ]
        })
        fig = px.pie(results_dist, values='العدد', names='النتيجة',
                     color_discrete_sequence=['#16a34a', '#ca8a04', '#dc2626'], hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=14), showlegend=True,
                          legend=dict(orientation='h', yanchor='bottom', y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### ⚽ توزيع الأهداف")
        total_goals = df['home_goals'] + df['away_goals']
        fig = px.histogram(x=total_goals, nbins=range(0, int(total_goals.max()) + 2),
                           labels={'x': 'إجمالي الأهداف', 'y': 'عدد المباريات'},
                           color_discrete_sequence=['#3b82f6'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=14),
                          xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                          yaxis=dict(gridcolor='rgba(255,255,255,0.1)'))
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🌍 توزيع المباريات حسب الدوري")
    league_counts = df['league'].value_counts().head(15)
    fig = px.bar(x=league_counts.index, y=league_counts.values,
                 labels={'x': 'الدوري', 'y': 'عدد المباريات'},
                 color=league_counts.values, color_continuous_scale='Blues')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='white', size=12),
                      xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickangle=45),
                      yaxis=dict(gridcolor='rgba(255,255,255,0.1)'))
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════
# تبويب 3: أداء النماذج
# ═══════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## 🤖 أداء نماذج التعلم الآلي")
    
    if st.session_state.training_results:
        results = st.session_state.training_results
        ensemble_acc = (results['rf_accuracy'] * 0.30 + results['xgb_accuracy'] * 0.45 + results['lr_accuracy'] * 0.25)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #16a34a;">{results["rf_accuracy"]:.1%}</div><div class="metric-label">Random Forest</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #3b82f6;">{results["xgb_accuracy"]:.1%}</div><div class="metric-label">XGBoost</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #ca8a04;">{results["lr_accuracy"]:.1%}</div><div class="metric-label">Logistic Regression</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #a855f7;">{ensemble_acc:.1%}</div><div class="metric-label">Ensemble (مجمع)</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📊 مقارنة دقة النماذج")
        
        model_comparison = pd.DataFrame({
            'النموذج': ['Random Forest', 'XGBoost', 'Logistic Regression', 'Ensemble'],
            'الدقة': [results['rf_accuracy'], results['xgb_accuracy'], results['lr_accuracy'], ensemble_acc]
        })
        
        fig = px.bar(model_comparison, x='النموذج', y='الدقة', color='النموذج',
                     color_discrete_sequence=['#16a34a', '#3b82f6', '#ca8a04', '#a855f7'],
                     text='الدقة', text_auto='.1%')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=14),
                          xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                          yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickformat='.0%'),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🔄 التحقق المتقاطع (Cross-Validation)")
        st.info(f"""
        **Random Forest 5-Fold CV:**
        - المتوسط: **{results['rf_cv_mean']:.3f}**
        - الانحراف المعياري: **{results['rf_cv_std']:.3f}**
        - حجم بيانات الاختبار: **{results['test_size']}** مباراة
        """)
    else:
        st.warning("لم يتم تدريب النماذج بعد.")

# ═══════════════════════════════════════════════════════
# تبويب 4: أهمية الميزات
# ═══════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 📋 أهمية الميزات في التنبؤ")
    
    if st.session_state.models and st.session_state.models.is_trained:
        importance = st.session_state.models.get_feature_importance()
        importance_df = pd.DataFrame({
            'الميزة': list(importance.keys()),
            'الأهمية': list(importance.values())
        }).sort_values('الأهمية', ascending=True)
        
        fig = px.bar(importance_df, x='الأهمية', y='الميزة', orientation='h',
                     color='الأهمية', color_continuous_scale='Blues')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=12),
                          xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                          yaxis=dict(gridcolor='rgba(255,255,255,0.1)'), height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📊 تفاصيل الميزات")
        st.dataframe(importance_df.sort_values('الأهمية', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("لم يتم تدريب النماذج بعد.")

# ═══════════════════════════════════════════════════════
# تبويب 5: الدليل
# ═══════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## 📚 دليل استخدام النظام")
    st.markdown("""
    ### 🎯 نظرة عامة
    **محلل المباريات الذكي** هو نظام متقدم للتنبؤ بنتائج مباريات كرة القدم باستخدام:
    - **3 نماذج تعلم آلي** (Random Forest, XGBoost, Logistic Regression)
    - **8 عوامل تحليلية متطورة**
    - **بيانات من 50+ دوري عالمي**
    
    ### 📊 العوامل التحليلية الثمانية
    
    | # | العامل | الوصف |
    |---|--------|-------|
    | 1 | **شكل الفريق** | آخر 5 نتائج (W=3, D=1, L=0) |
    | 2 | **القوة الهجومية** | الأهداف المسجلة + xG لكل مباراة |
    | 3 | **القوة الدفاعية** | معكوس الأهداف المستقبلة + xG ضد |
    | 4 | **ميزة الملعب** | نسبة النقاط في الملعب/خارجه |
    | 5 | **تاريخ المواجهات** | آخر 10 مواجهات مباشرة |
    | 6 | **الانضباط** | البطاقات الصفراء والحمراء |
    | 7 | **كفاءة التسديد** | الأهداف / التسديدات على المرمى |
    | 8 | **زخم الأداء** | اتجاه الأداء (تصاعدي/تنازلي) |
    
    ### 🤖 النماذج المستخدمة
    1. **Random Forest** - نموذج Ensemble يجمع بين 200 شجرة قرار
    2. **XGBoost** - Gradient Boosting متقدم (أعلى وزن في Ensemble)
    3. **Logistic Regression** - نموذج أساسي قابل للتفسير
    
    ### 📈 كيفية الاستخدام
    1. اختر **فريق أصحاب الأرض** و**فريق الضيف**
    2. اضغط على زر **"تنبأ بالنتيجة"**
    3. شاهد الاحتمالات والعوامل التحليلية
    4. قارن بين تنبؤات النماذج الثلاثة
    
    ### ⚠️ إخلاء المسؤولية
    هذا النظام للأغراض التحليلية والتعليمية فقط. النتائج ليست توصيات للمراهنة.
    """)
    st.markdown("---")
    st.markdown("### 📞 للتواصل والدعم")
    st.info("للاستفسارات والاقتراحات، يرجى التواصل عبر القنوات الرسمية.")

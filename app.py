"""
ProBet - Football Prediction App
Advanced football match prediction using ML
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import plotly.express as px

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scrapers.data_fetcher import FootballDataFetcher
from src.analysis.advanced_analyzer import AdvancedFootballAnalyzer
from src.models.prediction_models import FootballPredictionModels

# Page config
st.set_page_config(
    page_title="ProBet - Football Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    * { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .main-header {
        font-size: 3rem; font-weight: 900; text-align: center;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6, #1e3a8a);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 15px; padding: 1.5rem; border: 1px solid #334155; text-align: center;
    }
    .metric-value { font-size: 2.5rem; font-weight: 900; color: #3b82f6; }
    .metric-label { color: #94a3b8; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# Session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None
    st.session_state.analyzer = None
    st.session_state.models = None
    st.session_state.training_results = None

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")
    st.markdown("### 📥 Data Source")
    data_source = st.radio("Source:", ["Sample Data", "Upload CSV"], index=0)
    if data_source == "Upload CSV":
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
    st.markdown("---")
    st.info("🏆 50+ Leagues\n🤖 3 ML Models\n📊 8 Factors\n⚡ Instant")
    st.markdown("---")
    st.caption("© 2026 ProBet")

# Header
st.markdown('<div class="main-header">⚽ ProBet Football Predictor</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748b; font-size: 1.2rem;">AI-powered football match prediction system</p>', unsafe_allow_html=True)

# Load data
if not st.session_state.data_loaded:
    with st.spinner("🔄 Loading and analyzing data..."):
        fetcher = FootballDataFetcher()
        if data_source == "Sample Data":
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
        st.success(f"✅ Loaded {len(df)} matches with {len(X.columns)} features!")

# Main tabs
tabs = st.tabs(["🔮 Predict Match", "📊 Analytics", "🤖 Model Performance", "📋 Features", "📚 Guide"])

# Tab 1: Prediction
with tabs[0]:
    st.markdown("## 🔮 Match Prediction")
    
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 Home Team:", sorted(st.session_state.df['home_team'].unique()), index=0)
    with col2:
        away_team = st.selectbox("✈️ Away Team:", sorted([t for t in st.session_state.df['away_team'].unique() if t != home_team]), index=0)
    
    if st.button("🔮 Predict Result", type="primary", use_container_width=True):
        with st.spinner("🧠 Analyzing..."):
            factors = st.session_state.analyzer.get_all_factors(home_team, away_team)
            
            single_match = pd.DataFrame([{
                'home_team': home_team, 'away_team': away_team,
                'home_goals': 0, 'away_goals': 0,
                'date': pd.Timestamp.now(), 'league': 'Unknown', 'season': '2024-25'
            }])
            
            X_pred = st.session_state.models.prepare_features(single_match, st.session_state.analyzer)
            prediction = st.session_state.models.predict(X_pred)
            
            st.markdown("---")
            
            # Teams display
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.markdown(f"<h2 style='text-align: center; color: #3b82f6;'>{home_team}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #94a3b8;'>🏠 Home</p>", unsafe_allow_html=True)
            with c2:
                st.markdown("<h1 style='text-align: center; color: #f59e0b;'>VS</h1>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<h2 style='text-align: center; color: #ef4444;'>{away_team}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #94a3b8;'>✈️ Away</p>", unsafe_allow_html=True)
            
            # Probabilities
            st.markdown("### 📊 Result Probabilities")
            probs = prediction['probabilities']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dc2626, #991b1b); border-radius: 15px; padding: 1.5rem; text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs['away_win']}%</div>
                    <div style="color: #fecaca; margin-top: 0.5rem;">{away_team} Win</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ca8a04, #854d0e); border-radius: 15px; padding: 1.5rem; text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs['draw']}%</div>
                    <div style="color: #fef08a; margin-top: 0.5rem;">Draw</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #16a34a, #166534); border-radius: 15px; padding: 1.5rem; text-align: center;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs['home_win']}%</div>
                    <div style="color: #bbf7d0; margin-top: 0.5rem;">{home_team} Win</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Final prediction
            pred_class = prediction['ensemble_class']
            confidence = prediction['confidence']
            
            if pred_class == 'home_win':
                color, emoji = '#16a34a', '🏆'
            elif pred_class == 'draw':
                color, emoji = '#ca8a04', '🤝'
            else:
                color, emoji = '#dc2626', '✈️'
            
            st.markdown(f"""
            <div style="background: {color}; border-radius: 15px; padding: 1.5rem; text-align: center; margin-top: 1rem;">
                <div style="font-size: 1.8rem; font-weight: 900; color: white;">{emoji} Prediction: {prediction['ensemble_prediction']}</div>
                <div style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">Confidence: {confidence}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Factors
            st.markdown("---")
            st.markdown("### 📈 Analysis Factors (8 Factors)")
            
            factor_data = {
                'Factor': [
                    'Form (Last 5)', 'Offensive Strength', 'Defensive Strength',
                    'Home/Away Advantage', 'Head-to-Head', 'Discipline',
                    'Shot Efficiency', 'Momentum'
                ],
                f'{home_team}': [
                    f"{factors['home_form']:.2f}", f"{factors['home_offense']:.2f}",
                    f"{factors['home_defense']:.2f}", f"{factors['home_advantage']:.2f}",
                    f"{factors['h2h_home']:.2f}", f"{factors['home_discipline']:.2f}",
                    f"{factors['home_efficiency']:.2f}", f"{factors['home_momentum']:.2f}"
                ],
                f'{away_team}': [
                    f"{factors['away_form']:.2f}", f"{factors['away_offense']:.2f}",
                    f"{factors['away_defense']:.2f}", f"{factors['away_advantage']:.2f}",
                    f"{1 - factors['h2h_home'] - factors['h2h_draw']:.2f}",
                    f"{factors['away_discipline']:.2f}",
                    f"{factors['away_efficiency']:.2f}", f"{factors['away_momentum']:.2f}"
                ]
            }
            factor_df = pd.DataFrame(factor_data)
            st.dataframe(factor_df, use_container_width=True, hide_index=True)
            
            # Model comparison
            st.markdown("---")
            st.markdown("### 🤖 Model Comparison")
            models_comp = prediction['individual_models']
            model_comparison_data = []
            for model_name, model_data in models_comp.items():
                model_comparison_data.append({
                    'Model': model_name.replace('_', ' ').title(),
                    'Prediction': model_data['prediction'],
                    'Away Win': f"{model_data['probabilities']['away_win']:.1f}%",
                    'Draw': f"{model_data['probabilities']['draw']:.1f}%",
                    'Home Win': f"{model_data['probabilities']['home_win']:.1f}%"
                })
            comp_df = pd.DataFrame(model_comparison_data)
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

# Tab 2: Analytics
with tabs[1]:
    st.markdown("## 📊 Analytics Dashboard")
    df = st.session_state.df
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df):,}</div><div class="metric-label">Total Matches</div></div>', unsafe_allow_html=True)
    with col2:
        avg_goals = (df['home_goals'].sum() + df['away_goals'].sum()) / len(df)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_goals:.2f}</div><div class="metric-label">Avg Goals/Match</div></div>', unsafe_allow_html=True)
    with col3:
        home_win_pct = ((df['home_goals'] > df['away_goals']).sum() / len(df)) * 100
        st.markdown(f'<div class="metric-card"><div class="metric-value">{home_win_pct:.1f}%</div><div class="metric-label">Home Win Rate</div></div>', unsafe_allow_html=True)
    with col4:
        draw_pct = ((df['home_goals'] == df['away_goals']).sum() / len(df)) * 100
        st.markdown(f'<div class="metric-card"><div class="metric-value">{draw_pct:.1f}%</div><div class="metric-label">Draw Rate</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Result Distribution")
        results_dist = pd.DataFrame({
            'Result': ['Home Win', 'Draw', 'Away Win'],
            'Count': [
                (df['home_goals'] > df['away_goals']).sum(),
                (df['home_goals'] == df['away_goals']).sum(),
                (df['home_goals'] < df['away_goals']).sum()
            ]
        })
        fig = px.pie(results_dist, values='Count', names='Result',
                     color_discrete_sequence=['#16a34a', '#ca8a04', '#dc2626'], hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=14))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### ⚽ Goals Distribution")
        total_goals = df['home_goals'] + df['away_goals']
        fig = px.histogram(x=total_goals, nbins=range(0, int(total_goals.max()) + 2),
                           labels={'x': 'Total Goals', 'y': 'Matches'},
                           color_discrete_sequence=['#3b82f6'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=14))
        st.plotly_chart(fig, use_container_width=True)

# Tab 3: Model Performance
with tabs[2]:
    st.markdown("## 🤖 Model Performance")
    
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
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #a855f7;">{ensemble_acc:.1%}</div><div class="metric-label">Ensemble</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📊 Accuracy Comparison")
        
        model_comparison = pd.DataFrame({
            'Model': ['Random Forest', 'XGBoost', 'Logistic Regression', 'Ensemble'],
            'Accuracy': [results['rf_accuracy'], results['xgb_accuracy'], results['lr_accuracy'], ensemble_acc]
        })
        
        fig = px.bar(model_comparison, x='Model', y='Accuracy', color='Model',
                     color_discrete_sequence=['#16a34a', '#3b82f6', '#ca8a04', '#a855f7'],
                     text='Accuracy', text_auto='.1%')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=14), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🔄 Cross-Validation")
        st.info(f"""
        **Random Forest 5-Fold CV:**
        - Mean: **{results['rf_cv_mean']:.3f}**
        - Std: **{results['rf_cv_std']:.3f}**
        - Test size: **{results['test_size']}** matches
        """)

# Tab 4: Features
with tabs[3]:
    st.markdown("## 📋 Feature Importance")
    
    if st.session_state.models and st.session_state.models.is_trained:
        importance = st.session_state.models.get_feature_importance()
        importance_df = pd.DataFrame({
            'Feature': list(importance.keys()),
            'Importance': list(importance.values())
        }).sort_values('Importance', ascending=True)
        
        fig = px.bar(importance_df, x='Importance', y='Feature', orientation='h',
                     color='Importance', color_continuous_scale='Blues')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='white', size=12), height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📊 Feature Details")
        st.dataframe(importance_df.sort_values('Importance', ascending=False), use_container_width=True, hide_index=True)

# Tab 5: Guide
with tabs[4]:
    st.markdown("## 📚 User Guide")
    st.markdown("""
    ### 🎯 Overview
    **ProBet** is an advanced football prediction system using:
    - **3 ML Models** (Random Forest, XGBoost, Logistic Regression)
    - **8 Analysis Factors**
    - **50+ Global Leagues**
    
    ### 📊 8 Analysis Factors
    
    | # | Factor | Description |
    |---|--------|-------------|
    | 1 | **Form** | Last 5 results (W=3, D=1, L=0) |
    | 2 | **Offensive Strength** | Goals + xG per match |
    | 3 | **Defensive Strength** | Inverse of conceded goals |
    | 4 | **Home/Away Advantage** | Points ratio home/away |
    | 5 | **Head-to-Head** | Last 10 direct matches |
    | 6 | **Discipline** | Yellow/red cards |
    | 7 | **Shot Efficiency** | Goals / shots on target |
    | 8 | **Momentum** | Performance trend |
    
    ### 🤖 Models
    1. **Random Forest** - 200 trees ensemble
    2. **XGBoost** - Advanced gradient boosting
    3. **Logistic Regression** - Interpretable baseline
    
    ### ⚠️ Disclaimer
    For analytical and educational purposes only. Not betting advice.
    """)

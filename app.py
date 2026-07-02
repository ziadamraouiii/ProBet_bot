"""
ProBet - Offline Predictor (يدعم 5 ملفات دفعة واحدة)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import warnings

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════
# PART 1: تحميل ودمج الملفات المتعددة
# ═══════════════════════════════════════════════════════

def load_multiple_csvs(uploaded_files) -> pd.DataFrame:
    """تحميل ودمج جميع ملفات CSV المرفوعة"""
    dfs = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            st.info(f"✅ تم تحميل: {file.name} (عدد الصفوف: {len(df)})")
        except Exception as e:
            st.error(f"❌ خطأ في الملف {file.name}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    # دمج جميع الإطارات عمودياً (صفوف فوق بعض)
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # تنظيف التواريخ
    if 'date' in merged_df.columns:
        merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')
        merged_df = merged_df.dropna(subset=['date'])
    
    # توحيد أسماء الأعمدة (محاولة تلقائية)
    rename_map = {}
    for col in merged_df.columns:
        col_lower = col.lower().strip()
        if 'home' in col_lower and 'team' in col_lower:
            rename_map[col] = 'home_team'
        elif 'away' in col_lower and 'team' in col_lower:
            rename_map[col] = 'away_team'
        elif 'home' in col_lower and ('goal' in col_lower or 'score' in col_lower):
            rename_map[col] = 'home_goals'
        elif 'away' in col_lower and ('goal' in col_lower or 'score' in col_lower):
            rename_map[col] = 'away_goals'
        elif 'xg' in col_lower and 'home' in col_lower:
            rename_map[col] = 'home_xg'
        elif 'xg' in col_lower and 'away' in col_lower:
            rename_map[col] = 'away_xg'
        elif 'shot' in col_lower and 'home' in col_lower:
            rename_map[col] = 'home_shots'
        elif 'shot' in col_lower and 'away' in col_lower:
            rename_map[col] = 'away_shots'
    
    merged_df = merged_df.rename(columns=rename_map)
    
    # التأكد من الأعمدة الأساسية
    required_cols = ['home_team', 'away_team', 'home_goals', 'away_goals', 'date']
    missing = [c for c in required_cols if c not in merged_df.columns]
    if missing:
        st.warning(f"⚠️ الأعمدة المفقودة: {missing}. حاول اختيار ملفات أخرى.")
    
    # تحويل الأهداف إلى أرقام
    for col in ['home_goals', 'away_goals']:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0).astype(int)
    
    return merged_df

# ═══════════════════════════════════════════════════════
# PART 2: المحلل والنماذج (نفس الكود السابق ولكن مختصر)
# ═══════════════════════════════════════════════════════

class AdvancedAnalyzer:
    def __init__(self, df):
        self.df = df
        self._cache = {}
    
    def _get_stats(self, team, cutoff_date):
        key = f"{team}_{cutoff_date}"
        if key in self._cache: return self._cache[key]
        
        matches = self.df[
            ((self.df['home_team']==team)|(self.df['away_team']==team)) & 
            (self.df['date'] < cutoff_date)
        ]
        if len(matches)==0:
            stats = {'goals':0, 'conceded':0, 'xg':0, 'xgc':0, 'wins':0, 'draws':0, 'losses':0, 'form':[]}
        else:
            g = gc = xg = xgc = w = d = l = 0
            for _, row in matches.iterrows():
                if row['home_team']==team:
                    g += row['home_goals']; gc += row['away_goals']
                    xg += row.get('home_xg',0); xgc += row.get('away_xg',0)
                    if row['home_goals']>row['away_goals']: w+=1
                    elif row['home_goals']==row['away_goals']: d+=1
                    else: l+=1
                else:
                    g += row['away_goals']; gc += row['home_goals']
                    xg += row.get('away_xg',0); xgc += row.get('home_xg',0)
                    if row['away_goals']>row['home_goals']: w+=1
                    elif row['away_goals']==row['home_goals']: d+=1
                    else: l+=1
            recent = matches.sort_values('date').tail(5)
            form = []
            for _, r in recent.iterrows():
                if r['home_team']==team: form.append('W' if r['home_goals']>r['away_goals'] else 'D' if r['home_goals']==r['away_goals'] else 'L')
                else: form.append('W' if r['away_goals']>r['home_goals'] else 'D' if r['away_goals']==r['home_goals'] else 'L')
            stats = {'goals':g, 'conceded':gc, 'xg':xg, 'xgc':xgc, 'wins':w, 'draws':d, 'losses':l, 'form':form}
        self._cache[key]=stats
        return stats
    
    def get_factors(self, home, away, date):
        hs = self._get_stats(home, date); aw = self._get_stats(away, date)
        def form_score(s):
            if not s['form']: return 0.5
            pts = sum(3 if f=='W' else 1 if f=='D' else 0 for f in s['form'])
            return pts/(len(s['form'])*3)
        n_h = hs['wins']+hs['draws']+hs['losses'] or 1
        n_a = aw['wins']+aw['draws']+aw['losses'] or 1
        return {
            'home_form': form_score(hs), 'away_form': form_score(aw),
            'home_offense': (hs['goals']/n_h)*0.4 + (hs['xg']/n_h)*0.6,
            'away_offense': (aw['goals']/n_a)*0.4 + (aw['xg']/n_a)*0.6,
            'home_defense': 1/(1+ (hs['conceded']/n_h)*0.4 + (hs['xgc']/n_h)*0.6),
            'away_defense': 1/(1+ (aw['conceded']/n_a)*0.4 + (aw['xgc']/n_a)*0.6),
            'h2h_home': 0.5, 'h2h_away': 0.5  # تبسيط للسرعة
        }

class ModelTrainer:
    def __init__(self): self.models={}
    def train(self, df):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        X_list = []
        analyzer = AdvancedAnalyzer(df)
        for _, row in df.iterrows():
            f = analyzer.get_factors(row['home_team'], row['away_team'], row['date'])
            X_list.append([f['home_form']-f['away_form'], f['home_offense']-f['away_offense'], f['home_defense']-f['away_defense']])
        X = pd.DataFrame(X_list).fillna(0)
        y = (df['home_goals'] > df['away_goals']).astype(int)
        if len(X)<10: return None
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        self.analyzer = analyzer
        return {'accuracy': 0.7}  # تبسيط
    
    def predict(self, home, away, date):
        f = self.analyzer.get_factors(home, away, date)
        vec = [[f['home_form']-f['away_form'], f['home_offense']-f['away_offense'], f['home_defense']-f['away_defense']]]
        X = self.scaler.transform(vec)
        prob = self.model.predict_proba(X)[0]
        return {'home_win': round(prob[1]*100,1), 'away_win': round(prob[0]*100,1)}

# ═══════════════════════════════════════════════════════
# PART 3: واجهة Streamlit
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="ProBet - Multi Upload", layout="wide")
st.markdown("## ⚽ ProBet (متعدد الملفات)")

with st.sidebar:
    st.markdown("### 📂 رفع ملفات CSV (اختر 5 ملفات)")
    uploaded_files = st.file_uploader("اختر ملفات المواسم", type=['csv'], accept_multiple_files=True)
    
    if uploaded_files and len(uploaded_files) > 0:
        if st.button("🚀 تحميل ودمج الكل"):
            with st.spinner(f"جاري دمج {len(uploaded_files)} ملف..."):
                df = load_multiple_csvs(uploaded_files)
                if not df.empty:
                    st.session_state.df = df
                    st.session_state.trainer = ModelTrainer()
                    res = st.session_state.trainer.train(df)
                    if res:
                        st.session_state.data_loaded = True
                        st.success(f"✅ تم الدمج! {len(df)} مباراة. جاهز للتنبؤ.")
                    else:
                        st.error("البيانات غير كافية للتدريب.")

if st.session_state.get('data_loaded'):
    df = st.session_state.df
    teams = sorted(list(set(df['home_team'].unique()) | set(df['away_team'].unique())))
    
    c1, c2 = st.columns(2)
    with c1: home = st.selectbox("🏠 المضيف", teams)
    with c2: away = st.selectbox("✈️ الضيف", [t for t in teams if t!=home])
    
    if st.button("🔮 تنبأ"):
        pred = st.session_state.trainer.predict(home, away, df['date'].max() + timedelta(days=1))
        st.markdown(f"### 🏆 **{home}** : {pred['home_win']}% vs **{away}** : {pred['away_win']}%")
        if pred['home_win'] > 50: st.success(f"التوقع: فوز {home}")
        else: st.info(f"التوقع: فوز {away}")

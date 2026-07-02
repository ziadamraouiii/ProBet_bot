"""
ProBet - التنبؤ بنتائج المباريات (يدعم full_time_home/away)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import zipfile
import io
import warnings

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════
# PART 1: تحميل ودمج الملفات (مع دعم full_time_home/away)
# ═══════════════════════════════════════════════════════

def load_and_merge_files(uploaded_files) -> pd.DataFrame:
    """تحميل الملفات ودمجها مع دعم أعمدة full_time_home و full_time_away"""
    dfs = {}
    
    for file in uploaded_files:
        file_name = file.name.lower()
        try:
            if file_name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(file.read())) as z:
                    for csv_file in z.namelist():
                        if csv_file.endswith('.csv'):
                            with z.open(csv_file) as f:
                                df = pd.read_csv(f)
                                key = csv_file.split('/')[-1].lower()
                                dfs[key] = df
                                st.info(f"✅ فك ضغط: {file_name} → {csv_file} (صفوف: {len(df)})")
            else:
                df = pd.read_csv(file)
                dfs[file_name] = df
                st.info(f"✅ تحميل: {file_name} (صفوف: {len(df)})")
        except Exception as e:
            st.error(f"❌ خطأ في {file_name}: {e}")
    
    # 1. التحقق من وجود الملفات الأساسية
    if 'matches.csv' not in dfs:
        st.error("❌ لم يتم العثور على matches.csv")
        return pd.DataFrame()
    
    matches = dfs['matches.csv'].copy()
    
    # 2. معالجة التاريخ (من utc_date)
    if 'utc_date' in matches.columns:
        matches['date'] = pd.to_datetime(matches['utc_date'], errors='coerce')
        matches = matches.dropna(subset=['date'])
        st.success("✅ تم استخراج التاريخ من utc_date")
    else:
        st.error("❌ لا يوجد عمود utc_date في matches.csv")
        return pd.DataFrame()
    
    # 3. ربط أسماء الفرق من teams.csv
    if 'teams.csv' in dfs:
        teams = dfs['teams.csv']
        id_col = None
        name_col = None
        for col in teams.columns:
            col_low = col.lower().strip()
            if col_low in ['id', 'team_id', 'teamid']:
                id_col = col
            if col_low in ['name', 'team', 'team_name']:
                name_col = col
        
        if id_col and name_col:
            matches = matches.merge(teams[[id_col, name_col]], left_on='home_team_id', right_on=id_col, how='left')
            matches = matches.rename(columns={name_col: 'home_team'})
            matches = matches.drop(columns=[id_col])
            
            matches = matches.merge(teams[[id_col, name_col]], left_on='away_team_id', right_on=id_col, how='left')
            matches = matches.rename(columns={name_col: 'away_team'})
            matches = matches.drop(columns=[id_col])
            
            st.success("✅ تم ربط أسماء الفرق من teams.csv")
        else:
            st.warning(f"⚠️ لم يتم العثور على أعمدة ID/Name في teams.csv")
    else:
        st.warning("⚠️ لم يتم رفع teams.csv، سيتم استخدام المعرفات كأسماء")
        matches['home_team'] = matches['home_team_id'].astype(str)
        matches['away_team'] = matches['away_team_id'].astype(str)
    
    # 4. جلب الأهداف من scores.csv (مع دعم full_time_home/away)
    if 'scores.csv' in dfs:
        scores = dfs['scores.csv']
        st.info(f"📄 scores.csv الأعمدة: {list(scores.columns)}")
        
        home_goal_col = None
        away_goal_col = None
        
        # قائمة الكلمات المفتاحية للبحث (مرتبة حسب الأفضلية)
        home_keywords = ['full_time_home', 'ft_home', 'home_goals', 'hgoal', 'home_score', 'goals_home', 'score_home']
        away_keywords = ['full_time_away', 'ft_away', 'away_goals', 'agoal', 'away_score', 'goals_away', 'score_away']
        
        for col in scores.columns:
            col_low = col.lower().strip()
            for kw in home_keywords:
                if kw in col_low:
                    home_goal_col = col
                    break
            if home_goal_col:
                break
        
        for col in scores.columns:
            col_low = col.lower().strip()
            for kw in away_keywords:
                if kw in col_low:
                    away_goal_col = col
                    break
            if away_goal_col:
                break
        
        if home_goal_col and away_goal_col:
            # ربط باستخدام match_id
            match_id_col = None
            for col in ['match_id', 'id', 'fixture_id']:
                if col in matches.columns and col in scores.columns:
                    match_id_col = col
                    break
            
            if match_id_col:
                scores_subset = scores[[match_id_col, home_goal_col, away_goal_col]]
                matches = matches.merge(scores_subset, on=match_id_col, how='left')
                matches = matches.rename(columns={home_goal_col: 'home_goals', away_goal_col: 'away_goals'})
                st.success(f"✅ تم ربط الأهداف الحقيقية من scores.csv (أعمدة: {home_goal_col}, {away_goal_col})")
            else:
                st.warning("⚠️ لا يوجد عمود match_id مشترك للربط مع scores.csv")
        else:
            st.warning(f"⚠️ لم يتم العثور على أعمدة الأهداف في scores.csv. الأعمدة الموجودة: {list(scores.columns)}")
    else:
        st.warning("⚠️ لم يتم رفع scores.csv")
    
    # 5. إذا لم توجد أعمدة الأهداف، نستخدم عمود winner كحل احتياطي
    if 'home_goals' not in matches.columns or 'away_goals' not in matches.columns:
        if 'winner' in matches.columns:
            st.info("ℹ️ باستخدام عمود winner لتحديد الفائز (توليد أهداف وهمية للتدريب)")
            matches['home_goals'] = 0
            matches['away_goals'] = 0
            for idx, row in matches.iterrows():
                if row['winner'] == 'HOME_TEAM':
                    matches.at[idx, 'home_goals'] = 2
                    matches.at[idx, 'away_goals'] = 1
                elif row['winner'] == 'AWAY_TEAM':
                    matches.at[idx, 'home_goals'] = 1
                    matches.at[idx, 'away_goals'] = 2
                else:  # DRAW
                    matches.at[idx, 'home_goals'] = 1
                    matches.at[idx, 'away_goals'] = 1
            st.success("✅ تم توليد أهداف وهمية من عمود winner")
        else:
            st.error("❌ لا يوجد أهداف ولا عمود winner للاستدلال")
            return pd.DataFrame()
    
    # 6. التأكد من وجود الأعمدة النهائية
    required = ['home_team', 'away_team', 'home_goals', 'away_goals', 'date']
    missing = [col for col in required if col not in matches.columns]
    if missing:
        st.error(f"❌ الأعمدة المفقودة: {missing}")
        st.info(f"الأعمدة الموجودة: {list(matches.columns)}")
        return pd.DataFrame()
    
    # تنظيف البيانات
    matches['home_goals'] = pd.to_numeric(matches['home_goals'], errors='coerce').fillna(0).astype(int)
    matches['away_goals'] = pd.to_numeric(matches['away_goals'], errors='coerce').fillna(0).astype(int)
    matches = matches.dropna(subset=['home_team', 'away_team'])
    
    # الاحتفاظ بالأعمدة المطلوبة فقط
    matches = matches[required]
    
    return matches

# ═══════════════════════════════════════════════════════
# PART 2: المحلل والنماذج
# ═══════════════════════════════════════════════════════

class AdvancedAnalyzer:
    def __init__(self, df):
        self.df = df
        self._cache = {}
    
    def _get_stats(self, team, cutoff_date):
        key = f"{team}_{cutoff_date}"
        if key in self._cache:
            return self._cache[key]
        
        matches = self.df[
            ((self.df['home_team'] == team) | (self.df['away_team'] == team)) &
            (self.df['date'] < cutoff_date)
        ]
        if len(matches) == 0:
            stats = {'goals': 0, 'conceded': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'form': []}
        else:
            g = gc = w = d = l = 0
            for _, row in matches.iterrows():
                if row['home_team'] == team:
                    g += row['home_goals']
                    gc += row['away_goals']
                    if row['home_goals'] > row['away_goals']:
                        w += 1
                    elif row['home_goals'] == row['away_goals']:
                        d += 1
                    else:
                        l += 1
                else:
                    g += row['away_goals']
                    gc += row['home_goals']
                    if row['away_goals'] > row['home_goals']:
                        w += 1
                    elif row['away_goals'] == row['home_goals']:
                        d += 1
                    else:
                        l += 1
            recent = matches.sort_values('date').tail(5)
            form = []
            for _, r in recent.iterrows():
                if r['home_team'] == team:
                    form.append('W' if r['home_goals'] > r['away_goals'] else 'D' if r['home_goals'] == r['away_goals'] else 'L')
                else:
                    form.append('W' if r['away_goals'] > r['home_goals'] else 'D' if r['away_goals'] == r['home_goals'] else 'L')
            stats = {'goals': g, 'conceded': gc, 'wins': w, 'draws': d, 'losses': l, 'form': form}
        self._cache[key] = stats
        return stats
    
    def get_factors(self, home, away, date):
        hs = self._get_stats(home, date)
        aw = self._get_stats(away, date)
        
        def form_score(s):
            if not s['form']:
                return 0.5
            pts = sum(3 if f == 'W' else 1 if f == 'D' else 0 for f in s['form'])
            return pts / (len(s['form']) * 3)
        
        n_h = hs['wins'] + hs['draws'] + hs['losses'] or 1
        n_a = aw['wins'] + aw['draws'] + aw['losses'] or 1
        
        return {
            'home_form': form_score(hs),
            'away_form': form_score(aw),
            'home_offense': hs['goals'] / n_h,
            'away_offense': aw['goals'] / n_a,
            'home_defense': 1 / (1 + hs['conceded'] / n_h),
            'away_defense': 1 / (1 + aw['conceded'] / n_a),
        }

class ModelTrainer:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.analyzer = None
    
    def train(self, df):
        if len(df) < 10:
            st.error("البيانات قليلة جداً (تحتاج على الأقل 10 مباريات).")
            return None
        
        analyzer = AdvancedAnalyzer(df)
        X_list = []
        for _, row in df.iterrows():
            f = analyzer.get_factors(row['home_team'], row['away_team'], row['date'])
            X_list.append([
                f['home_form'] - f['away_form'],
                f['home_offense'] - f['away_offense'],
                f['home_defense'] - f['away_defense']
            ])
        X = pd.DataFrame(X_list).fillna(0)
        y = (df['home_goals'] > df['away_goals']).astype(int)
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        self.model.fit(X_scaled, y)
        self.analyzer = analyzer
        
        acc = self.model.score(X_scaled, y)
        return {'accuracy': acc, 'samples': len(df)}
    
    def predict(self, home, away, date):
        if self.model is None:
            raise ValueError("النموذج لم يُدرب بعد!")
        f = self.analyzer.get_factors(home, away, date)
        vec = [[
            f['home_form'] - f['away_form'],
            f['home_offense'] - f['away_offense'],
            f['home_defense'] - f['away_defense']
        ]]
        X = self.scaler.transform(vec)
        prob = self.model.predict_proba(X)[0]
        return {
            'home_win': round(prob[1] * 100, 1),
            'away_win': round(prob[0] * 100, 1),
            'confidence': round(max(prob) * 100, 1)
        }

# ═══════════════════════════════════════════════════════
# PART 3: واجهة Streamlit
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="ProBet - النهائي", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #1e3a8a, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚽ ProBet - التنبؤ (النسخة النهائية)</div>', unsafe_allow_html=True)

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None
    st.session_state.trainer = None

with st.sidebar:
    st.markdown("## 📂 رفع الملفات")
    st.caption("ارفع جميع ملفاتك (matches, teams, scores, ...)")
    uploaded_files = st.file_uploader(
        "اختر الملفات (CSV أو ZIP)",
        type=['csv', 'zip'],
        accept_multiple_files=True
    )
    
    if uploaded_files and len(uploaded_files) > 0:
        if st.button("🚀 تحميل ودمج الكل", type="primary"):
            with st.spinner("جاري المعالجة..."):
                df = load_and_merge_files(uploaded_files)
                if not df.empty:
                    st.session_state.df = df
                    st.session_state.trainer = ModelTrainer()
                    res = st.session_state.trainer.train(df)
                    if res:
                        st.session_state.data_loaded = True
                        st.success(f"✅ تم التدريب! {len(df)} مباراة. الدقة: {res['accuracy']:.1%}")
                    else:
                        st.error("فشل التدريب.")
                else:
                    st.error("لم يتم الحصول على بيانات صالحة.")

if st.session_state.get('data_loaded') and st.session_state.df is not None:
    df = st.session_state.df
    teams = sorted(list(set(df['home_team'].unique()) | set(df['away_team'].unique())))
    
    st.markdown(f"**📊 عدد الفرق:** {len(teams)} | **عدد المباريات:** {len(df)}")
    
    st.markdown("---")
    st.markdown("## 🔮 تنبؤ مباراة جديدة")
    
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 الفريق المضيف", teams, index=0)
    with col2:
        away_options = [t for t in teams if t != home_team]
        away_team = st.selectbox("✈️ الفريق الضيف", away_options, index=0 if away_options else 0)
    
    last_date = df['date'].max()
    match_date = last_date + timedelta(days=1)
    
    if st.button("🔮 تنبأ", type="primary"):
        with st.spinner("تحليل العوامل..."):
            try:
                pred = st.session_state.trainer.predict(home_team, away_team, match_date)
                st.markdown("---")
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1:
                    st.markdown(f"<h3 style='text-align:center;color:#3b82f6;'>{home_team}</h3>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<h1 style='text-align:center;color:#f59e0b;'>⚡</h1>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<h3 style='text-align:center;color:#ef4444;'>{away_team}</h3>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                col_a.metric(f"فوز {home_team}", f"{pred['home_win']}%")
                col_b.metric(f"فوز {away_team}", f"{pred['away_win']}%")
                
                st.progress(pred['home_win'] / 100, text=f"ثقة النموذج: {pred['confidence']}%")
                
                if pred['home_win'] > 60:
                    st.success(f"🏆 التوقع: **{home_team}** هو الأقرب للفوز!")
                elif pred['away_win'] > 60:
                    st.success(f"🏆 التوقع: **{away_team}** هو الأقرب للفوز!")
                else:
                    st.warning("⚠️ المباراة متكافئة، احتمال التعادل كبير!")
            except Exception as e:
                st.error(f"خطأ في التنبؤ: {e}")
    
    with st.expander("📊 إحصائيات سريعة"):
        col1, col2, col3 = st.columns(3)
        col1.metric("المباريات الكلية", len(df))
        avg_goals = (df['home_goals'].sum() + df['away_goals'].sum()) / len(df)
        col2.metric("متوسط الأهداف", f"{avg_goals:.2f}")
        home_win_rate = (df['home_goals'] > df['away_goals']).sum() / len(df) * 100
        col3.metric("نسبة فوز الأرض", f"{home_win_rate:.1f}%")
else:
    st.info("📂 **يرجى رفع الملفات من القائمة الجانبية.**")
    st.markdown("""
    ### 📋 التعليمات:
    1. ارفع جميع الملفات (matches.csv, teams.csv, scores.csv, ...)
    2. اضغط على 'تحميل ودمج الكل'
    3. التطبيق سيتعرف على `full_time_home` و `full_time_away` تلقائياً
    4. اختر فريقين واضغط 'تنبأ'
    """)

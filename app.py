import streamlit as st
import pandas as pd
import sqlite3
import math
from openai import OpenAI
import os

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO")

# 2. قائمة الرهانات الاستراتيجية
MY_BETS = [
    "فوز الفريق المضيف (1)", "فوز الفريق الضيف (2)", "التعادل (X)",
    "أكثر من 2.5 أهداف (Over 2.5)", "أقل من 2.5 أهداف (Under 2.5)",
    "كلا الفريقين يسجل (BTTS - Yes)", "فريق واحد فقط يسجل (BTTS - No)",
    "فوز المضيف أو تعادل (1X)", "فوز الضيف أو تعادل (2X)", "لا للتعادل (12)"
]

# 3. دوال العمليات
def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def calculate_match_probabilities(home_xg, away_xg):
    def p_func(x, mu): return (math.exp(-mu) * (mu**x)) / math.factorial(x)
    hw, d, aw, o25, btts = 0.0, 0.0, 0.0, 0.0, 0.0
    for i in range(6):
        for j in range(6):
            prob = p_func(i, home_xg) * p_func(j, away_xg)
            if i > j: hw += prob
            elif i == j: d += prob
            else: aw += prob
            if (i + j) > 2.5: o25 += prob
            if i > 0 and j > 0: btts += prob
    return hw, d, aw, o25, btts

# 4. الواجهة التفاعلية
try:
    leagues = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")['tournament_name'].tolist()
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues)
    teams = sorted(get_db_data("SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?", (selected_league, selected_league)).iloc[:, 0].tolist())
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)
except:
    st.error("خطأ في تحميل قاعدة البيانات")

# 5. زر التحليل (المحرك)
if st.button("🚀 تشغيل محرك التحليل"):
    query = """
    SELECT home_team, away_team, home_score, away_score 
    FROM cached_matches 
    WHERE tournament_name = ? AND 
    ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))
    """
    match_info = get_db_data(query, (selected_league, home_team, away_team, away_team, home_team))
    
    if not match_info.empty:
        home_xg = match_info[match_info['home_team'] == home_team]['home_score'].mean()
        away_xg = match_info[match_info['away_team'] == away_team]['away_score'].mean()
        
        hw, d, aw, o25, btts = calculate_match_probabilities(home_xg, away_xg)
        probs = {'hw': hw, 'd': d, 'aw': aw, 'o25': o25, 'btts': btts}
        
        # الاتصال بالذكاء الاصطناعي (محدث لـ OpenModel)
        try:
            client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.openmodel.ai/" 
)


            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"مباراة {home_team} vs {away_team}. نسب بويسون: {probs}. اختر أفضل رهان من: {MY_BETS}"}]
            )
            st.info(response.choices[0].message.content)
        except Exception as e:
            st.error(f"خطأ اتصال: {e}")
    else:
        st.warning("لا توجد بيانات لهذه المباراة")

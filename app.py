import streamlit as st
import pandas as pd
import sqlite3
import math
from openai import OpenAI
import os

# إعدادات الواجهة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO")

# قائمة الرهانات الاستراتيجية
MY_BETS = [
    "فوز الفريق المضيف (1)", "فوز الفريق الضيف (2)", "التعادل (X)",
    "أكثر من 2.5 أهداف (Over 2.5)", "أقل من 2.5 أهداف (Under 2.5)",
    "كلا الفريقين يسجل (BTTS - Yes)", "فريق واحد فقط يسجل (BTTS - No)",
    "فوز المضيف أو تعادل (1X)", "فوز الضيف أو تعادل (2X)", "لا للتعادل (12)"
]

def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def calculate_match_probabilities(home_xg, away_xg):
    # توزيع بويسون للمحاكاة
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

# جلب الدوري والفرق
try:
    leagues = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")['tournament_name'].tolist()
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues)
    teams = sorted(get_db_data("SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?", (selected_league, selected_league)).iloc[:, 0].tolist())
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)
except:
    st.error("خطأ في تحميل قاعدة البيانات")

if st.button("🚀 تشغيل محرك التحليل"):
    query = """
    SELECT home_team, away_team, home_score, away_score 
    FROM cached_matches 
    WHERE tournament_name = ? AND 
    ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))
    """
    df = get_db_data(query, (selected_league, home_team, away_team, away_team, home_team))
    
    if not df.empty:
        home_xg = df[df['home_team'] == home_team]['home_score'].mean() if not df[df['home_team'] == home_team].empty else 1.2
        away_xg = df[df['away_team'] == away_team]['away_score'].mean() if not away_xg == 0 else 1.0
        
        hw, d, aw, o25, btts = calculate_match_probabilities(home_xg, away_xg)
        probs = {'hw': hw, 'd': d, 'aw': aw, 'o25': o25, 'btts': btts}
        
        st.write(f"نسب فوز المضيف: {hw:.1%}")
        
        try:
            client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"حلل مباراة {home_team} ضد {away_team} بناءً على نسب بويسون {probs} واختر الأفضل من قائمة: {MY_BETS}"}]
            )
            st.info(response.choices[0].message.content)
        except Exception as e:
            st.error(f"خطأ في الاتصال بالذكاء الاصطناعي: {e}")
    else:
        st.warning("لا توجد بيانات لهذه المباراة")

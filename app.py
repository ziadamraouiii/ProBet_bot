import streamlit as st
import pandas as pd
import sqlite3
import math
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO")

# 2. قائمة الرهانات الاستراتيجية
MY_BETS = [
    "فوز المضيف (1)", "فوز الضيف (2)", "التعادل (X)",
    "أكثر من 2.5 أهداف (Over 2.5)", "أقل من 2.5 أهداف (Under 2.5)",
    "كلا الفريقين يسجل (BTTS - Yes)", "فريق واحد فقط يسجل (BTTS - No)"
]

# 3. دالة جلب البيانات
def get_db_data(query, params=()):
    try:
        conn = sqlite3.connect('analytics_v6.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# 4. دالة الحساب الرياضي
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

# 5. دالة الاتصال الجديدة (حسب توثيق OpenModel)
def get_ai_analysis(content):
    url = "https://api.openmodel.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-v4-flash",
        "input": content
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            # استخراج النص بناءً على الهيكلية الجديدة
            return response.json().get('output', str(response.json()))
        else:
            return f"خطأ {response.status_code}: {response.text}"
    except Exception as e:
        return f"خطأ تقني: {str(e)}"

# 6. الواجهة الرئيسية
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
if not leagues_df.empty:
    leagues = leagues_df['tournament_name'].tolist()
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues)
    
    teams = sorted(get_db_data("SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?", (selected_league, selected_league)).iloc[:, 0].tolist())
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)

    if st.button("🚀 تشغيل محرك التحليل"):
        query = "SELECT home_team, away_team, home_score, away_score FROM cached_matches WHERE tournament_name = ? AND ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))"
        match_info = get_db_data(query, (selected_league, home_team, away_team, away_team, home_team))
        
        if not match_info.empty:
            home_xg = match_info[match_info['home_team'] == home_team]['home_score'].mean()
            away_xg = match_info[match_info['away_team'] == away_team]['away_score'].mean()
            
            hw, d, aw, o25, btts = calculate_match_probabilities(home_xg, away_xg)
            probs = f"HW:{hw:.2f}, D:{d:.2f}, AW:{aw:.2f}, O25:{o25:.2f}"
            
            analysis_prompt = f"حلل مباراة {home_team} ضد {away_team} بناءً على نسب بويسون: {probs}. اقترح رهان واحد قوي."
            
            with st.spinner('جاري التحليل...'):
                result = get_ai_analysis(analysis_prompt)
                st.info(result)
        else:
            st.warning("⚠️ لا توجد بيانات كافية.")
else:
    st.error("قاعدة البيانات فارغة أو غير متصلة.")

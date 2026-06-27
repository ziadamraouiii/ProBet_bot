import streamlit as st
import pandas as pd
import sqlite3
import os
from openai import OpenAI

# إعداد العميل (السرية مضمونة من إعدادات Streamlit)
api_key = st.secrets.get("DEEPSEEK_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")

def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_ai_analysis(stats_summary):
    prompt = f"""
    أنت خبير إحصائي ومحلل مراهنات رياضي. 
    قم بتحليل هذه البيانات الإحصائية للمباريات الأخيرة:
    {stats_summary}
    استخدم توزيع بويسون (Poisson Distribution) لتقدير احتمالات تسجيل الأهداف، وقارن ذلك بالمعطيات.
    أعطني: 1. أفضل رهان، 2. نسبة الثقة، 3. التحليل الإحصائي المختصر.
    أجب باللغة العربية فقط.
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# الواجهة
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
leagues = leagues_df['tournament_name'].tolist()

if leagues:
    selected_league = st.selectbox("اختر الدوري:", leagues)
    teams_query = "SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?"
    teams = sorted(get_db_data(teams_query, (selected_league, selected_league)).iloc[:, 0].tolist())
    
    home_team = st.selectbox("الفريق المضيف", teams)
    away_team = st.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة بالذكاء الاصطناعي"):
        match_query = "SELECT * FROM cached_matches WHERE tournament_name = ? AND ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))"
        match_info = get_db_data(match_query, (selected_league, home_team, away_team, away_team, home_team))
        
        if not match_info.empty:
            stats_summary = match_info.to_string()
            with st.spinner('جاري التحليل الإحصائي وتقدير بويسون...'):
                analysis = get_ai_analysis(stats_summary)
                st.markdown("### 🤖 توصية المحلل الذكي:")
                st.info(analysis)
        else:
            st.warning("⚠️ لا توجد بيانات للمباراة المختارة.")

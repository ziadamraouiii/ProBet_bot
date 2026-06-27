import streamlit as st
import pandas as pd
import sqlite3
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO - النظام الاحترافي")

# 2. دالة جلب البيانات
def get_db_data(query, params=()):
    try:
        conn = sqlite3.connect('analytics_v6.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

# 3. محرك التحليل الذكي (تم تحديثه ليتناسب مع هيكل الرد الجديد)
def get_ai_analysis(prompt):
    url = "https://api.openmodel.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {"model": "gpt-5.5", "input": prompt}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            
            # محاولة استخراج النص بناءً على الهيكل الذي كشفناه
            # إذا كان النص داخل 'output' أو 'content' أو مسار فرعي
            if 'output' in data:
                return str(data['output'])
            elif 'content' in data:
                return str(data['content'])
            else:
                return f"الرد نجح لكن المسار غير معروف. هيكل الرد: {str(data)[:200]}"
        else:
            return f"خطأ API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"خطأ برمجـي: {str(e)}"

# 4. واجهة المستخدم
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
if not leagues_df.empty:
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues_df['tournament_name'].tolist())
    
    teams = sorted(get_db_data("SELECT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT away_team FROM cached_matches WHERE tournament_name = ?", (selected_league, selected_league))['home_team'].tolist())
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)

    if st.button("🚀 تحليل الرهان الاستراتيجي"):
        data = get_db_data("SELECT home_score, away_score FROM cached_matches WHERE tournament_name = ? AND home_team = ? AND away_team = ?", (selected_league, home_team, away_team))
        
        if not data.empty:
            prompt = f"حلل مباراة {home_team} و {away_team}. قدم رهان واحد دقيق."
            
            with st.spinner('جاري التحليل...'):
                result = get_ai_analysis(prompt)
                st.success("✅ تحليل الذكاء الاصطناعي:")
                st.write(result)
        else:
            st.warning("⚠️ لا توجد بيانات للمواجهة المختارة.")

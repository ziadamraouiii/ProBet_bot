import streamlit as st
import pandas as pd
import sqlite3
import requests

st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO - المستشار الذكي")

def get_db_data(query, params=()):
    try:
        conn = sqlite3.connect('analytics_v6.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()

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
            # فحص هيكلي متقدم:
            # نحاول الوصول للمسار بالطريقة التي تظهر في التوثيق
            try:
                # المحاولة الأولى: المسار الذي ظهر في التوثيق
                return data['output'][0]['content'][0]['text']
            except (KeyError, IndexError):
                # إذا فشل، نرجع الـ JSON كاملاً لنعرف مكانه الصحيح
                return f"خطأ في مسار JSON. هيكل الرد هو: {str(data)[:500]}"
        else:
            return f"خطأ API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"خطأ تقني: {str(e)}"

# واجهة المستخدم (نفسها كما كانت)
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
if not leagues_df.empty:
    leagues = leagues_df['tournament_name'].tolist()
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues)
    
    teams_query = "SELECT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT away_team FROM cached_matches WHERE tournament_name = ?"
    teams = sorted(get_db_data(teams_query, (selected_league, selected_league))['home_team'].tolist())
    
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)

    if st.button("🚀 تشغيل التحليل"):
        data = get_db_data("SELECT home_score, away_score FROM cached_matches WHERE tournament_name = ? AND home_team = ? AND away_team = ?", (selected_league, home_team, away_team))
        
        if not data.empty:
            home_avg = data['home_score'].mean()
            away_avg = data['away_score'].mean()
            prompt = f"حلل مباراة {home_team} و {away_team}. المضيف {home_avg:.2f}، الضيف {away_avg:.2f}. قدم رهان واحد فقط."
            
            with st.spinner('جاري التحليل...'):
                result = get_ai_analysis(prompt)
                st.success("✅ تحليل الذكاء الاصطناعي:")
                st.write(result)
        else:
            st.warning("⚠️ لا توجد بيانات كافية.")

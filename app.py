import streamlit as st
import pandas as pd
import sqlite3
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO - النظام الاحترافي")

# 2. دالة جلب البيانات من قاعدة البيانات
def get_db_data(query, params=()):
    try:
        conn = sqlite3.connect('analytics_v6.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"خطأ في قاعدة البيانات: {e}")
        return pd.DataFrame()

# 3. دالة التحليل الذكي (متوافقة 100% مع التوثيق المرفق)
def get_ai_analysis(prompt):
    url = "https://api.openmodel.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    # ملاحظة: تأكد من اسم النموذج 'gpt-5.5' أو استبدله بما هو متاح في لوحة تحكمك
    payload = {
        "model": "gpt-5.5",
        "input": prompt
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            # المسار الدقيق وفقاً لهيكل JSON في التوثيق: output[0].content[0].text
            return data['output'][0]['content'][0]['text']
        else:
            return f"خطأ API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"خطأ في استخراج البيانات: {str(e)}"

# 4. واجهة المستخدم
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
if not leagues_df.empty:
    leagues = leagues_df['tournament_name'].tolist()
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues)
    
    # جلب الفرق بناءً على الدوري المختار
    teams_query = "SELECT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT away_team FROM cached_matches WHERE tournament_name = ?"
    teams = sorted(get_db_data(teams_query, (selected_league, selected_league))['home_team'].tolist())
    
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)

    if st.button("🚀 تشغيل تحليل البيانات"):
        # جلب إحصائيات المواجهات المباشرة
        match_query = "SELECT home_score, away_score FROM cached_matches WHERE tournament_name = ? AND home_team = ? AND away_team = ?"
        data = get_db_data(match_query, (selected_league, home_team, away_team))
        
        if not data.empty:
            home_avg = data['home_score'].mean()
            away_avg = data['away_score'].mean()
            
            prompt = f"حلل مباراة {home_team} و {away_team}. المضيف يسجل متوسط {home_avg:.2f}، الضيف يسجل متوسط {away_avg:.2f}. قدم توقعاً دقيقاً لرهان واحد."
            
            with st.spinner('جاري التحليل عبر OpenModel...'):
                result = get_ai_analysis(prompt)
                st.success("✅ تحليل الذكاء الاصطناعي:")
                st.write(result)
        else:
            st.warning("⚠️ لا تتوفر إحصائيات كافية لهذه المواجهة.")
else:
    st.error("قاعدة البيانات لا تحتوي على دوريات.")

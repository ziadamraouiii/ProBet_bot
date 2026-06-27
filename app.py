import streamlit as st
import pandas as pd
import sqlite3
import math
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO - المستشار الذكي")

# 2. دالة جلب البيانات مع تنظيف للأسماء لضمان عدم وجود أخطاء
def get_db_data(query, params=()):
    try:
        conn = sqlite3.connect('analytics_v6.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# 3. محرك التحليل (الاتصال المباشر بـ OpenModel عبر /v1/responses)
def get_ai_analysis(prompt):
    url = "https://api.openmodel.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-v4-flash",
        "input": prompt
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get('output', "لم يتم استلام نص من الخادم")
        else:
            return f"خطأ الاتصال ({response.status_code}): {response.text}"
    except Exception as e:
        return f"خطأ برمجـي: {str(e)}"

# 4. واجهة التطبيق
leagues = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")['tournament_name'].tolist()
selected_league = st.selectbox("🏆 اختر الدوري:", leagues)

# جلب الفرق المتاحة فعلياً في القاعدة
all_teams_df = get_db_data("SELECT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT away_team FROM cached_matches WHERE tournament_name = ?", (selected_league, selected_league))
teams = sorted(all_teams_df['home_team'].tolist())

home_team = st.selectbox("🏠 المضيف", teams)
away_team = st.selectbox("✈️ الضيف", teams)

if st.button("🚀 تحليل الرهان الاستراتيجي"):
    # سحب إحصائيات الفريقين
    match_query = """
        SELECT home_score, away_score 
        FROM cached_matches 
        WHERE tournament_name = ? AND home_team = ? AND away_team = ?
    """
    data = get_db_data(match_query, (selected_league, home_team, away_team))
    
    if not data.empty:
        # حساب الخلاصة الرياضية
        home_avg = data['home_score'].mean()
        away_avg = data['away_score'].mean()
        
        # إرسال الخلاصة (Summary) للذكاء الاصطناعي
        prompt = f"""
        أنت خبير رهانات رياضية. قم بتحليل مباراة {home_team} ضد {away_team}.
        البيانات التاريخية: المضيف يسجل متوسط {home_avg:.2f}، الضيف يسجل متوسط {away_avg:.2f}.
        بناءً على هذه الأرقام، قدم لي:
        1. أفضل رهان (1X2 أو Over/Under).
        2. نسبة الثقة في الرهان.
        3. سبب منطقي قصير جداً.
        """
        
        with st.spinner('جاري معالجة البيانات وبناء الاستراتيجية...'):
            analysis = get_ai_analysis(prompt)
            st.success("✅ النتيجة المحللة:")
            st.info(analysis)
    else:
        st.warning("⚠️ لا توجد مواجهات مباشرة مسجلة لهذه الفرق. جرب فرقاً أخرى.")

# توضيح هيكلية عمل البوت


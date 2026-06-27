import streamlit as st
import pandas as pd
import sqlite3
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.title("⚽ PENTAGON AI PRO - النظام الشامل")

# 2. دالة جلب البيانات
def get_db_data(query, params=()):
    try:
        conn = sqlite3.connect('analytics_v6.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"خطأ في القاعدة: {e}")
        return pd.DataFrame()

# 3. محرك التحليل الذكي
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
            if 'output' in data: return str(data['output'])
            if 'content' in data: return str(data['content'])
            return str(data)
        return f"خطأ API ({response.status_code})"
    except Exception as e:
        return f"خطأ: {str(e)}"

# 4. الواجهة والمنطق
leagues = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
if not leagues.empty:
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues['tournament_name'].tolist())
    
    teams = sorted(get_db_data("SELECT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT away_team FROM cached_matches WHERE tournament_name = ?", (selected_league, selected_league))['home_team'].tolist())
    home_team = st.selectbox("🏠 المضيف", teams)
    away_team = st.selectbox("✈️ الضيف", teams)

    if st.button("🚀 تشغيل التحليل الشامل"):
        # استعلام مرن يبحث عن الفريقين بغض النظر عن كونهما مضيف أو ضيف
        query = """
            SELECT home_score, away_score FROM cached_matches 
            WHERE tournament_name = ? AND (
                (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
            )
        """
        data = get_db_data(query, (selected_league, home_team, away_team, away_team, home_team))
        
        if not data.empty:
            home_avg = data['home_score'].mean()
            away_avg = data['away_score'].mean()
            
            prompt = f"مباراة {home_team} ضد {away_team}. المضيف سجل {home_avg:.2f} والضيف سجل {away_avg:.2f}. قدم رهان واحد دقيق."
            
            with st.spinner('جاري التحليل...'):
                result = get_ai_analysis(prompt)
                st.success("✅ النتيجة:")
                st.write(result)
        else:
            st.warning("⚠️ لا توجد بيانات للمواجهة. تأكد من تطابق الأسماء:")
            st.write("إليك قائمة الفرق المتاحة في هذا الدوري للتحقق من الأسماء:")
            st.dataframe(pd.DataFrame(teams, columns=["الفرق المتاحة"]))
else:
    st.error("قاعدة البيانات فارغة.")

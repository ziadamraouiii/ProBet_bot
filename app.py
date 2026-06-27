import streamlit as st
import pandas as pd
import sqlite3

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# 1. كود التشخيص: للتأكد من شكل البيانات في القاعدة
try:
    conn = sqlite3.connect('analytics_v6.db')
    sample = pd.read_sql_query("SELECT home_team, away_team FROM cached_matches LIMIT 5", conn)
    conn.close()
    st.write("🔍 معاينة سريعة للبيانات (تأكد من مطابقة هذه الأسماء لما تختاره):")
    st.write(sample)
except:
    st.write("القاعدة فارغة حالياً.")

# 2. دالة جلب الفرق (مع تنظيف المسافات)
def get_all_teams():
    conn = sqlite3.connect('analytics_v6.db')
    query = "SELECT DISTINCT home_team FROM cached_matches UNION SELECT DISTINCT away_team FROM cached_matches"
    df = pd.read_sql_query(query, conn)
    conn.close()
    # تنظيف الأسماء من أي مسافات زائدة
    return sorted([str(team).strip() for team in df.iloc[:, 0].dropna()])

# 3. دالة البحث المرن (تتجاهل الأحرف الكبيرة/الصغيرة والمسافات)
def get_match_data(home, away):
    conn = sqlite3.connect('analytics_v6.db')
    query = """
    SELECT * FROM cached_matches 
    WHERE LOWER(TRIM(home_team)) = LOWER(TRIM(?)) 
    AND LOWER(TRIM(away_team)) = LOWER(TRIM(?))
    """
    df = pd.read_sql_query(query, conn, params=(home, away))
    conn.close()
    return df

# واجهة المستخدم
teams = get_all_teams()
if teams:
    home_team = st.selectbox("الفريق المضيف", teams)
    away_team = st.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        match_info = get_match_data(home_team, away_team)
        
        if not match_info.empty:
            st.success("✅ تم العثور على بيانات!")
            st.dataframe(match_info)
        else:
            st.warning("⚠️ لا توجد بيانات لهذه المواجهة. تأكد من تطابق الأسماء في القائمة مع الأسماء في المعاينة أعلاه.")
else:
    st.info("جاري تحميل الفرق من قاعدة البيانات...")

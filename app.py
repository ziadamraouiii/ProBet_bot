import streamlit as st
import pandas as pd
import sqlite3

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# 1. دالة جلب الفرق "من قلب قاعدة البيانات"
def get_all_teams():
    try:
        conn = sqlite3.connect('analytics_v6.db')
        # جلب الفرق من الجدول الذي يتم تحديثه بواسطة الـ Action
        query = """
        SELECT home_team FROM cached_matches
        UNION
        SELECT away_team FROM cached_matches
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        # تنظيف وتحويل الأسماء لقائمة
        teams = sorted([str(t).strip() for t in df.iloc[:, 0].dropna().unique()])
        return teams
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return []

# 2. دالة البحث المرن
def get_match_data(home, away):
    conn = sqlite3.connect('analytics_v6.db')
    # البحث باستخدام الدوال النصية لضمان المطابقة
    query = """
    SELECT * FROM cached_matches 
    WHERE LOWER(TRIM(home_team)) = LOWER(TRIM(?)) 
    AND LOWER(TRIM(away_team)) = LOWER(TRIM(?))
    """
    df = pd.read_sql_query(query, conn, params=(home, away))
    conn.close()
    return df

# 3. عرض البيانات (الواجهة)
teams = get_all_teams()
if teams:
    st.write("اختر الفرق لإجراء التحليل:")
    home_team = st.selectbox("الفريق المضيف", teams)
    away_team = st.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        match_info = get_match_data(home_team, away_team)
        
        if not match_info.empty:
            st.success("✅ تم العثور على بيانات المباراة!")
            st.dataframe(match_info)
        else:
            st.warning("⚠️ لم يتم العثور على بيانات لهذه المواجهة في قاعدة البيانات.")
else:
    st.info("جاري تحميل الفرق من قاعدة البيانات، يرجى الانتظار...")

# 4. كود التشخيص (يمكنك حذفه لاحقاً)
st.sidebar.markdown("---")
if st.sidebar.button("عرض عينة بيانات للتشخيص"):
    conn = sqlite3.connect('analytics_v6.db')
    sample = pd.read_sql_query("SELECT * FROM cached_matches LIMIT 5", conn)
    conn.close()
    st.sidebar.dataframe(sample)

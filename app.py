import streamlit as st
import pandas as pd
import sqlite3

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# 1. دالة جلب الفرق (تستخرج الأسماء الفريدة من القاعدة لضمان المطابقة)
def get_all_teams():
    try:
        conn = sqlite3.connect('analytics_v6.db')
        query = """
        SELECT home_team FROM cached_matches
        UNION
        SELECT away_team FROM cached_matches
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        # تنظيف القائمة من الفراغات
        teams = sorted([str(t).strip() for t in df.iloc[:, 0].dropna().unique()])
        return teams
    except Exception as e:
        st.error(f"خطأ في تحميل الفرق: {e}")
        return []

# 2. دالة البحث التبادلي (تجد المباراة سواء كانت Home أو Away)
def get_match_data(home, away):
    conn = sqlite3.connect('analytics_v6.db')
    # البحث يبحث في كلا الاتجاهين (A ضد B) أو (B ضد A)
    query = """
    SELECT * FROM cached_matches 
    WHERE (LOWER(TRIM(home_team)) = LOWER(TRIM(?)) AND LOWER(TRIM(away_team)) = LOWER(TRIM(?)))
    OR (LOWER(TRIM(home_team)) = LOWER(TRIM(?)) AND LOWER(TRIM(away_team)) = LOWER(TRIM(?)))
    """
    df = pd.read_sql_query(query, conn, params=(home, away, away, home))
    conn.close()
    return df

# 3. الواجهة الأمامية
teams = get_all_teams()

if teams:
    st.write("### اختر الفرق للتحليل:")
    home_team = st.selectbox("الفريق المضيف", teams)
    away_team = st.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        match_info = get_match_data(home_team, away_team)
        
        if not match_info.empty:
            st.success("✅ تم العثور على بيانات المباراة!")
            st.dataframe(match_info)
        else:
            st.warning("⚠️ لا توجد بيانات لهذه المواجهة في قاعدة البيانات.")
            st.info("تأكد أن البيانات المحددة في ملف `update_script.py` تتضمن الفرق التي اخترتها.")
else:
    st.info("جاري تحميل الفرق... تأكد من وجود ملف `analytics_v6.db` في المسار الصحيح.")

# 4. زر تشخيص سريع (يظهر في القائمة الجانبية للتأكد من المحتوى)
if st.sidebar.button("فحص قاعدة البيانات"):
    conn = sqlite3.connect('analytics_v6.db')
    sample = pd.read_sql_query("SELECT * FROM cached_matches LIMIT 10", conn)
    conn.close()
    st.sidebar.dataframe(sample)

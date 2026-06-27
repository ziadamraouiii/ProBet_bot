import streamlit as st
import pandas as pd
import sqlite3

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="wide")
st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# 1. دالة جلب الفرق
def get_all_teams():
    try:
        conn = sqlite3.connect('analytics_v6.db')
        query = "SELECT home_team FROM cached_matches UNION SELECT away_team FROM cached_matches"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return sorted([str(t).strip() for t in df.iloc[:, 0].dropna().unique()])
    except:
        return []

# 2. الواجهة الأمامية
teams = get_all_teams()

if teams:
    col1, col2 = st.columns(2)
    home_team = col1.selectbox("الفريق المضيف", teams)
    away_team = col2.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        conn = sqlite3.connect('analytics_v6.db')
        
        # أداة تشخيص: التأكد من أسماء الأعمدة في القاعدة
        cursor = conn.execute("PRAGMA table_info(cached_matches)")
        columns = [row[1] for row in cursor.fetchall()]
        st.write("📋 أعمدة الجدول المكتشفة:", columns)

        # البحث التبادلي المرن
        query = """
        SELECT * FROM cached_matches 
        WHERE (LOWER(TRIM(home_team)) = LOWER(TRIM(?)) AND LOWER(TRIM(away_team)) = LOWER(TRIM(?)))
        OR (LOWER(TRIM(home_team)) = LOWER(TRIM(?)) AND LOWER(TRIM(away_team)) = LOWER(TRIM(?)))
        """
        match_info = pd.read_sql_query(query, conn, params=(home_team, away_team, away_team, home_team))
        
        if not match_info.empty:
            st.success("✅ تم العثور على بيانات!")
            st.dataframe(match_info)
        else:
            st.warning("⚠️ لم يتم العثور على مباراة بين الفريقين المختارين في الجدول.")
            # عرض عينة صغيرة لنرى الفرق الموجودة فعلياً
            st.write("🔎 عرض عينة من 5 مباريات في القاعدة للتأكد من الأسماء:")
            st.dataframe(pd.read_sql_query("SELECT home_team, away_team FROM cached_matches LIMIT 5", conn))
        
        conn.close()
else:
    st.error("لم يتم العثور على قاعدة بيانات أو أنها فارغة.")

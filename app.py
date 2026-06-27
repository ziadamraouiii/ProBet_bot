import streamlit as st
import pandas as pd
import sqlite3

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# دالة الاتصال بالقاعدة
def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# 1. اختيار الدوري أولاً
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
leagues = leagues_df['tournament_name'].tolist()

if leagues:
    selected_league = st.selectbox("اختر الدوري:", leagues)
    
    # 2. فلترة الفرق بناءً على الدوري المختار
    teams_query = """
    SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ?
    UNION
    SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?
    """
    teams = sorted(get_db_data(teams_query, (selected_league, selected_league)).iloc[:, 0].tolist())
    
    col1, col2 = st.columns(2)
    home_team = col1.selectbox("الفريق المضيف", teams)
    away_team = col2.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        # البحث التبادلي
        match_query = """
        SELECT * FROM cached_matches 
        WHERE tournament_name = ? 
        AND ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))
        """
        match_info = get_db_data(match_query, (selected_league, home_team, away_team, away_team, home_team))
        
        if not match_info.empty:
            st.success("✅ تم العثور على بيانات المباراة!")
            st.dataframe(match_info)
        else:
            st.warning("⚠️ لا توجد بيانات مسجلة لهذه المواجهة في قاعدة البيانات.")
else:
    st.info("جاري تهيئة البيانات... يرجى التأكد من عمل الـ GitHub Action.")

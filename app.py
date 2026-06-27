import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")

def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# 1. جلب الدوريات
leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
leagues = leagues_df['tournament_name'].tolist()

if leagues:
    selected_league = st.selectbox("اختر الدوري:", leagues)
    
    # 2. جلب الفرق
    teams_query = "SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ? UNION SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?"
    teams = sorted(get_db_data(teams_query, (selected_league, selected_league)).iloc[:, 0].tolist())
    
    home_team = st.selectbox("الفريق المضيف", teams)
    away_team = st.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        # فحص الحقيقة: ماذا يوجد في القاعدة لهذا الدوري؟
        st.write("🔎 فحص البيانات (Debug):")
        check_query = "SELECT home_team, away_team FROM cached_matches WHERE tournament_name = ? LIMIT 10"
        st.dataframe(get_db_data(check_query, (selected_league,)))
        
        # البحث الفعلي
        match_query = """
        SELECT * FROM cached_matches 
        WHERE tournament_name = ? 
        AND (LOWER(TRIM(home_team)) = LOWER(TRIM(?)) OR LOWER(TRIM(away_team)) = LOWER(TRIM(?)))
        """
        match_info = get_db_data(match_query, (selected_league, home_team, home_team))
        
        if not match_info.empty:
            st.success("✅ تم العثور على بيانات!")
            st.dataframe(match_info)
        else:
            st.warning("⚠️ لا توجد مباراة مسجلة لهذين الفريقين في هذا الدوري.")
else:
    st.error("قاعدة البيانات فارغة! تأكد أن الـ GitHub Action يعمل بنجاح.")

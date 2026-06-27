import streamlit as st
import pandas as pd
import sqlite3
from core import calculate_poisson # تأكد من أن هذه الدالة تستقبل البيانات من DataFrame

# إعداد الصفحة
st.set_page_config(page_title="PRO BET AI", layout="centered")
st.title("⚽📊🔐 PRO BET AI")
st.markdown("---")

# 1. دالة جلب قائمة الفرق من قاعدة البيانات
def get_all_teams():
    try:
        # أضف هذا الكود بعد st.title
conn = sqlite3.connect('analytics_v6.db')
sample_data = pd.read_sql_query("SELECT * FROM cached_matches LIMIT 5", conn)
conn.close()
st.write("معاينة سريعة للبيانات في قاعدة البيانات:", sample_data)


# 2. دالة جلب بيانات مباراة معينة من قاعدة البيانات
def get_match_data(home, away):
    conn = sqlite3.connect('analytics_v6.db')
    # استخدام LIKE للبحث بمرونة أكبر (تجاهل حالة الأحرف)
    query = "SELECT * FROM cached_matches WHERE LOWER(TRIM(home_team)) = LOWER(TRIM(?)) AND LOWER(TRIM(away_team)) = LOWER(TRIM(?))"
    df = pd.read_sql_query(query, conn, params=(home, away))
    conn.close()
    return df


# واجهة المستخدم
teams = get_all_teams()
if teams:
    col1, col2 = st.columns(2)
    home_team = col1.selectbox("الفريق المضيف", teams)
    away_team = col2.selectbox("الفريق الضيف", teams)

    if st.button("تحليل المباراة"):
        match_info = get_match_data(home_team, away_team)
        
        if not match_info.empty:
            st.success("تم العثور على بيانات المباراة!")
            st.dataframe(match_info)
            
            # هنا يتم تمرير البيانات لخوارزمية بواسون
            # prediction = calculate_poisson(home_team, away_team)
            # st.write(prediction)
        else:
            st.warning("لا توجد بيانات لهذه المواجهة في قاعدة البيانات.")
else:
    st.info("جاري تحميل الفرق...")

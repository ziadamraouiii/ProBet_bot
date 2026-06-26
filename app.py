import streamlit as st
import pandas as pd
import sqlite3
from core import calculate_poisson, get_moving_average_stats
from data_engine import get_team_data

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")

st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# دالة لجلب قائمة الفرق الفريدة من قاعدة البيانات
def get_all_teams():
    try:
        conn = sqlite3.connect('analytics_v6.db')
        cursor = conn.cursor()
        # هذا الاستعلام سيعرض لنا أسماء كل الجداول في القاعدة
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        st.write("الجداول الموجودة في القاعدة هي:", tables) # هذا السطر سيظهر لك أسماء الجداول في الموقع
        conn.close()
        return []
    except Exception as e:
        st.error(f"خطأ: {e}")
        return []


# جلب قائمة الفرق
teams_list = get_all_teams()

# إدخال البيانات باستخدام القوائم المنسدلة
col1, col2 = st.columns(2)
with col1:
    h_team = st.selectbox("الفريق المضيف (Home)", teams_list)
with col2:
    a_team = st.selectbox("الفريق الضيف (Away)", teams_list)

if st.button("🚀 تحليل المباراة"):
    if h_team == a_team:
        st.warning("يرجى اختيار فريقين مختلفين!")
    else:
        try:
            # 1. جلب البيانات الخام من قاعدة البيانات
            h_data = get_team_data(h_team)
            a_data = get_team_data(a_team)
            
            if not h_data or not a_data:
                st.error("لم يتم العثور على بيانات كافية للفريقين في قاعدة البيانات.")
            else:
                # 2. حساب المتوسطات المتحركة
                h_s, h_c = get_moving_average_stats(h_data)
                a_s, a_c = get_moving_average_stats(a_data)
                
                # 3. حساب التوقعات (معادلة بواسون)
                h_exp = (h_s + a_c) / 2
                a_exp = (a_s + h_c) / 2
                
                win, draw, lose = calculate_poisson(h_exp, a_exp)
                
                # 4. عرض النتائج باحترافية
                st.subheader("📊 النتائج المتوقعة")
                c1, c2, c3 = st.columns(3)
                c1.metric("فوز المضيف", f"{round(win*100, 1)}%")
                c2.metric("التعادل", f"{round(draw*100, 1)}%")
                c3.metric("فوز الضيف", f"{round(lose*100, 1)}%")
                
                st.markdown("---")
                st.info(f"متوسط أهداف المضيف: {h_s} - متوسط استقباله: {h_c}")
                st.info(f"متوسط أهداف الضيف: {a_s} - متوسط استقباله: {a_c}")
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء التحليل: {e}")

# تذييل بسيط
st.sidebar.markdown("---")
st.sidebar.write("✅ النظام يعمل الآن بدون تعليق")

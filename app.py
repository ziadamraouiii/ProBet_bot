import streamlit as st
import pandas as pd
from core import calculate_poisson, get_moving_average_stats
from data_engine import get_team_data

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")

st.title("⚽ PENTAGON AI PRO")
st.markdown("---")

# إدخال البيانات
col1, col2 = st.columns(2)
with col1:
    h_team = st.text_input("الفريق المضيف (Home)")
with col2:
    a_team = st.text_input("الفريق الضيف (Away)")

if st.button("🚀 تحليل المباراة"):
    if not h_team or not a_team:
        st.warning("يرجى إدخال أسماء الفريقين!")
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

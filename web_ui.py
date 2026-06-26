import streamlit as st
from core import calculate_poisson, get_moving_average_stats
from data_engine import get_team_data

st.title("PENTAGON AI PRO")

h_team = st.text_input("المضيف")
a_team = st.text_input("الضيف")

if st.button("تحليل احترافي"):
    h_data = get_team_data(h_team)
    a_data = get_team_data(a_team)
    
    h_s, h_c = get_moving_average_stats(h_data)
    a_s, a_c = get_moving_average_stats(a_data)
    
    # حساب التوقعات
    h_exp = (h_s + a_c) / 2
    a_exp = (a_s + h_c) / 2
    
    win, draw, lose = calculate_poisson(h_exp, a_exp)
    
    st.metric("احتمال فوز المضيف", f"{round(win*100, 1)}%")
    st.metric("احتمال التعادل", f"{round(draw*100, 1)}%")

import streamlit as st
import requests

st.title("⚽ PENTAGON AI PRO - النظام المصحح")

API_KEY = st.secrets["RAPIDAPI_KEY"]
# أضفت sport_id=1 (لكرة القدم)
HEADERS = {
    "x-rapidapi-key": API_KEY, 
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

if st.button("تحليل المباريات (بإضافة sport_id)"):
    # قمت بإضافة sport_id=1 ليتجاوز خطأ الـ 400
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/live"
    params = {"sport_id": "1"} 
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            st.success("تم الاتصال بنجاح!")
            st.json(data)
        else:
            st.error(f"خطأ {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"فشل: {e}")

import streamlit as st
import requests

st.title("🛠️ فاحص الـ API")

API_KEY = st.secrets["RAPIDAPI_KEY"]
headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "flashscore4.p.rapidapi.com"}

if st.button("اختبار الاتصال بـ Flashscore"):
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/live"
    try:
        response = requests.get(url, headers=headers)
        st.write(f"الحالة (Status Code): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.write("البيانات المستلمة:")
            st.json(data) # هذا سيعرض لنا بالضبط ما يرسله الـ API
        else:
            st.error(f"خطأ: {response.text}")
    except Exception as e:
        st.error(f"فشل الاتصال: {e}")

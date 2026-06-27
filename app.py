import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", layout="wide")
st.title("⚽ PENTAGON AI PRO - النظام المتكامل")

# إعدادات الاتصال الخاصة بـ apifootball3
HEADERS = {
    "x-rapidapi-key": "c1f2624c03mshfd0d4445263443dp1964a4jsna5852c4b9947",
    "x-rapidapi-host": "apifootball3.p.rapidapi.com"
}

# 1. دالة جلب الدول (للتأكد من الاتصال)
@st.cache_data(ttl=3600)
def get_countries():
    url = "https://apifootball3.p.rapidapi.com/"
    params = {"action": "get_countries"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else []

# 2. دالة جلب المباريات (معدلة حسب action الخاص بـ apifootball3)
def get_matches():
    url = "https://apifootball3.p.rapidapi.com/"
    # ملاحظة: قم بتغيير 'get_fixtures' بناءً على توثيق الـ API الخاص بك
    params = {"action": "get_fixtures", "from": "2026-06-27", "to": "2026-06-30"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else []

# --- الواجهة ---
if st.button("اختبار الاتصال بالـ API"):
    countries = get_countries()
    st.write(f"تم الاتصال بنجاح! عدد الدول المتاحة: {len(countries)}")

matches = get_matches()
matches_map = {}

if matches:
    for match in matches:
        home = match.get('match_home_team_name', 'مجهول')
        away = match.get('match_away_team_name', 'مجهول')
        m_id = match.get('match_id')
        name = f"{home} vs {away}"
        matches_map[name] = m_id

    choice = st.selectbox("اختر مباراة:", list(matches_map.keys()))
    
    if st.button("تحليل"):
        st.success(f"المباراة المختارة: {choice} (ID: {matches_map[choice]})")
        st.write("الآن النظام جاهز لإرسال هذه البيانات للذكاء الاصطناعي.")
else:
    st.warning("جاري جلب المباريات أو أن الـ API لا يحتوي على مباريات في هذا التاريخ.")

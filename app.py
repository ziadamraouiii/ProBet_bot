import streamlit as st
import requests

st.title("⚽ PENTAGON AI PRO - النظام التشغيلي")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# دالة جلب المباريات الحية
def get_live_matches():
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/live"
    params = {"sport_id": "1"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else []

# جلب البيانات
data = get_live_matches()

# استخراج المباريات من الهيكل المعقد الذي ظهر في الصورة
matches_options = []
matches_map = {}

for tournament in data:
    for match in tournament.get('matches', []):
        name = f"{match['home']['name']} vs {match['away']['name']}"
        matches_options.append(name)
        matches_map[name] = match['match_id']

# واجهة المستخدم
choice = st.selectbox("اختر مباراة لتحليلها:", matches_options)

if st.button("تحليل المباراة"):
    match_id = matches_map[choice]
    st.write(f"المُعرّف المختار: {match_id}")
    # هنا سأقوم لاحقاً بإضافة استدعاء Get Match Stats باستخدام هذا الـ ID
    st.success("جاهز للتحليل! (الخطوة التالية: ربط إحصائيات المباراة بالذكاء الاصطناعي)")

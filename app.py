import streamlit as st
import requests

st.title("⚽ PENTAGON AI PRO - النظام المحصن")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

def get_live_matches():
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/live"
    params = {"sport_id": "1"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else []

data = get_live_matches()

matches_options = []
matches_map = {}

# التعديل هنا: إضافة حماية للبيانات
# استبدل حلقة for السابقة بهذا الكود لنعرف أين تكمن الأسماء
if data:
    st.write("هيكل أول مباراة وصلتنا (للتشخيص):")
    st.write(data[0].get('matches', [])[0]) # يعرض لنا بنية البيانات لنعرف كيف نستخرج منها الأسماء

            
            # نتجاهل المباريات التي لا تحتوي على أسماء فرق
            if home != 'Unknown' and away != 'Unknown':
                name = f"{home} vs {away}"
                matches_options.append(name)
                matches_map[name] = match['match_id']

# عرض النتائج
if matches_options:
    choice = st.selectbox("اختر مباراة لتحليلها:", matches_options)
    if st.button("تحليل المباراة"):
        match_id = matches_map[choice]
        st.write(f"المُعرّف المختار: {match_id}")
        st.success("الآن يمكننا سحب إحصائيات هذه المباراة!")
else:
    st.warning("لم يتم العثور على مباريات تحتوي على بيانات فرق كاملة حالياً.")

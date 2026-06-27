import streamlit as st
import requests

st.title("⚽ PENTAGON AI PRO - النظام المستقر")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 1. تهيئة الذاكرة إذا لم تكن موجودة
if 'matches_map' not in st.session_state:
    st.session_state.matches_map = {}

# 2. جلب البيانات (مرة واحدة فقط لتوفير الوقت)
@st.cache_data(ttl=60)
def get_live_matches():
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/live"
    params = {"sport_id": "1"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else []

data = get_live_matches()
matches_options = []
temp_map = {}

if data:
    for tournament in data:
        for match in tournament.get('matches', []):
            m_id = match.get('match_id')
            home = match.get('home', {}).get('name', 'فريق مجهول')
            away = match.get('away', {}).get('name', 'فريق مجهول')
            name = f"{home} vs {away} (ID: {m_id})"
            matches_options.append(name)
            temp_map[name] = m_id

# تحديث الذاكرة
st.session_state.matches_map = temp_map

# 3. واجهة الاختيار
choice = st.selectbox("اختر المباراة:", matches_options)

# 4. زر التحليل (باستخدام القيمة المحفوظة في session_state)
if st.button("تحليل المباراة المختارة"):
    if choice in st.session_state.matches_map:
        match_id = st.session_state.matches_map[choice]
        st.write(f"جاري تحليل المعرف: {match_id}")
        
        # هنا يتم استدعاء دالة الإحصائيات والذكاء الاصطناعي
        # (نفس الدوال السابقة التي عملت معك بنجاح)
        st.success("تم الربط بنجاح! الآن قم بدمج كود جلب الإحصائيات هنا.")
    else:
        st.error("خطأ في تحديد المباراة، حاول التحديث.")

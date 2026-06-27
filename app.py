import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", layout="wide")
st.title("⚽ PENTAGON AI PRO - النظام التشغيلي")

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

# هذا هو الكود المصحح للوصول لهيكل بياناتك الذي ظهر في الصورة
if isinstance(data, list):
    for tournament in data:
        # البحث عن المباريات داخل كل بطولة
        if 'matches' in tournament:
            for match in tournament['matches']:
                # استخراج المعرف
                m_id = match.get('match_id')
                
                # بناء اسم المباراة من خلال التحقق من وجود المفاتيح
                # استناداً لصورتك، الأسماء قد تكون مخفية في مكان أعمق، 
                # سنحاول الوصول لها أو عرض المعرف إذا لم تتوفر الأسماء
                home = match.get('home', {}).get('name', 'فريق مجهول')
                away = match.get('away', {}).get('name', 'فريق مجهول')
                
                name = f"{home} vs {away} (ID: {m_id})"
                matches_options.append(name)
                matches_map[name] = m_id

if matches_options:
    choice = st.selectbox("اختر المباراة:", matches_options)
    if st.button("تحليل"):
        m_id = matches_map[choice]
        st.write(f"تم اختيار المباراة: {m_id}")
        st.success("الآن النظام مستعد لسحب الإحصائيات!")
else:
    st.error("لم يتم العثور على مباريات في الهيكل الحالي. جرب تحديث الصفحة.")
    st.json(data[:1]) # لعرض بنية البيانات في حال استمرت المشكلة

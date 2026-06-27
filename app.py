import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO - القادمة", layout="wide")
st.title("🗓️ PENTAGON AI PRO - المباريات القادمة")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 1. جلب المباريات المجدولة فقط (Fixtures)
@st.cache_data(ttl=3600) # تحديث البيانات كل ساعة فقط
def get_upcoming_matches():
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/fixtures"
    params = {"sport_id": "1"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else []

# 2. جلب الإحصائيات (تظل كما هي)
def get_match_stats(match_id):
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats"
    params = {"match_id": match_id}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else None

# 3. تحليل الذكاء الاصطناعي
def analyze_with_ai(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.5", 
        "input": f"حلل إحصائيات المباراة القادمة: {str(stats_data)}. اقترح 3 رهانات (Odds > 1.5) مع تبرير إحصائي."
    }
    response = requests.post(url, headers=headers_ai, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data['output'][0]['content'][0]['text'] if 'output' in data else "لا توجد استجابة من الـ AI."
    return "خطأ في الاتصال."

# --- المعالجة ---
data = get_upcoming_matches()
matches_map = {}

if data:
    for tournament in data:
        for match in tournament.get('matches', []):
            # الآن الأسماء ستكون متوفرة لأن الـ API يرسلها في الـ Fixtures
            home = match.get('home', {}).get('name', 'فريق غير معروف')
            away = match.get('away', {}).get('name', 'فريق غير معروف')
            m_id = match.get('match_id')
            
            name = f"{home} vs {away}"
            matches_map[name] = m_id

    choice = st.selectbox("اختر المباراة القادمة:", list(matches_map.keys()))

    if st.button("تحليل المباراة"):
        m_id = matches_map[choice]
        with st.spinner('جاري سحب إحصائيات المواجهة المباشرة...'):
            stats = get_match_stats(m_id)
            if stats:
                report = analyze_with_ai(stats)
                st.success("🎯 تحليل الذكاء الاصطناعي:")
                st.write(report)
            else:
                st.warning("لا توجد إحصائيات كافية لهذه المباراة بعد. (جرب مباراة أخرى في دوري أكبر).")
else:
    st.info("جاري جلب المباريات القادمة...")

import streamlit as st
import requests

st.title("⚽ PENTAGON AI PRO - النظام المكتمل")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# دالة جلب الإحصائيات (تستخدم الـ ID الذي اخترته)
def get_match_stats(match_id):
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats"
    params = {"match_id": match_id}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else None

# دالة تحليل الذكاء الاصطناعي
def analyze_with_ai(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    prompt = f"حلل إحصائيات المباراة التالية: {str(stats_data)}. اقترح 2-3 رهانات آمنة (Odds > 1.5) مع تبرير إحصائي."
    response = requests.post(url, headers=headers_ai, json={"model": "gpt-5.5", "input": prompt})
    return response.json()['output'][0]['content'][0]['text']

# استعادة الـ Map من الـ session_state
if 'matches_map' not in st.session_state:
    st.session_state.matches_map = {}

# (ضع هنا كود جلب المباريات لملء الـ matches_options والـ map)
# ... [كود جلب المباريات من الرد السابق] ...

choice = st.selectbox("اختر المباراة:", list(st.session_state.matches_map.keys()))

if st.button("تحليل المباراة المختارة"):
    m_id = st.session_state.matches_map[choice]
    with st.spinner('جارٍ سحب الإحصائيات وتحليلها...'):
        stats = get_match_stats(m_id)
        if stats:
            report = analyze_with_ai(stats)
            st.success("🎯 تحليل الذكاء الاصطناعي:")
            st.write(report)
        else:
            st.error("تعذر جلب الإحصائيات. قد تكون المباراة انتهت أو البيانات غير متاحة.")

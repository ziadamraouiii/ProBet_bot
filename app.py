import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", layout="wide")
st.title("⚽ PENTAGON AI PRO - النظام المكتمل")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

def get_match_stats(match_id):
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats"
    params = {"match_id": match_id}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else None

def analyze_with_ai(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    
    payload = {
        "model": "gpt-5.5", 
        "input": f"حلل إحصائيات المباراة التالية: {str(stats_data)}. اقترح 2-3 رهانات آمنة (Odds > 1.5) مع تبرير إحصائي."
    }
    
    response = requests.post(url, headers=headers_ai, json=payload)
    
    # فحص الاستجابة بدلاً من الافتراض المباشر
    if response.status_code == 200:
        data = response.json()
        # هنا نتحقق هل المفاتيح موجودة قبل الوصول إليها
        if 'output' in data and len(data['output']) > 0:
            return data['output'][0]['content'][0]['text']
        else:
            return f"استجابة الـ AI غير مفهومة: {data}"
    else:
        return f"خطأ في الاتصال بالـ AI (كود {response.status_code}): {response.text}"

# إدارة المباريات
if 'matches_map' not in st.session_state:
    st.session_state.matches_map = {}

# (ضع هنا كود جلب المباريات لملء الـ matches_map)
# ...

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
            st.error("تعذر جلب الإحصائيات. قد تكون المباراة قد انتهت أو لا تتوفر إحصائيات تفصيلية لها حالياً.")

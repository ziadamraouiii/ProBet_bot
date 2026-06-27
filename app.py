import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO - النظام الفضاح", layout="wide")
st.title("⚽ PENTAGON AI PRO - أداة التشخيص الشاملة")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 1. الكود الفضاح (تشخيص الاتصال)
def get_upcoming_matches_debug():
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/fixtures"
    params = {"sport_id": "1"}
    
    with st.expander("🔍 كاشف الاتصال (اضغط هنا للمشاهدة)"):
        response = requests.get(url, headers=HEADERS, params=params)
        st.write(f"الحالة (Status Code): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.write("البيانات المستلمة (Raw Data):")
            st.json(data[:2])  # يعرض أول سجلين فقط
            return data
        else:
            st.error(f"خطأ في الاتصال: {response.text}")
            return []

# 2. منطق التحليل
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
        "input": f"حلل الإحصائيات: {str(stats_data)}. اعطني 3 رهانات آمنة مع التبرير."
    }
    
    response = requests.post(url, headers=headers_ai, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data['output'][0]['content'][0]['text'] if 'output' in data else "لا توجد استجابة."
    return "خطأ في الاتصال بالـ AI."

# --- التشغيل ---
data = get_upcoming_matches_debug()
matches_map = {}

if data:
    for tournament in data:
        for match in tournament.get('matches', []):
            home = match.get('home', {}).get('name', 'فريق غير معروف')
            away = match.get('away', {}).get('name', 'فريق غير معروف')
            m_id = match.get('match_id')
            
            name = f"{home} vs {away}"
            matches_map[name] = m_id

    choice = st.selectbox("اختر المباراة:", list(matches_map.keys()))

    if st.button("بدء التحليل الاحترافي"):
        m_id = matches_map[choice]
        stats = get_match_stats(m_id)
        if stats:
            report = analyze_with_ai(stats)
            st.success("🎯 تحليل الذكاء الاصطناعي:")
            st.write(report)
        else:
            st.error("تعذر جلب الإحصائيات لهذه المباراة المحددة.")
else:
    st.warning("لم يتم استلام أي بيانات من الـ API حالياً. (تأكد من حالة الاتصال في الكاشف أعلاه).")

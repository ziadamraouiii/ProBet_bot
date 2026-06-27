import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", page_icon="📈", layout="wide")
st.title("📈 PENTAGON AI PRO - النظام الاحترافي")

headers = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 1. جلب المباريات
def get_matches(status="live"):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/{status}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

# 2. جلب الإحصائيات
def get_match_stats(match_id):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats?match_id={match_id}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}

# 3. محرك التحليل الذكي
def analyze_betting_opportunities(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    prompt = f"حلل البيانات التالية: {str(stats_data)}. اقترح رهانين أو ثلاثة آمنة (Odds > 1.5) مع التبرير الإحصائي."
    response = requests.post(url, headers=headers_ai, json={"model": "gpt-5.5", "input": prompt})
    return response.json()['output'][0]['content'][0]['text'] if response.status_code == 200 else "خطأ في التحليل"

# 4. الواجهة (مع معالجة المتغير المفقود)
tab1, tab2 = st.tabs(["🔴 مباريات مباشرة", "🗓️ مباريات قادمة"])
selected_match_id = None # تعريف مبدئي

with tab1:
    live = get_matches("live")
    if live:
        choice = st.selectbox("اختر مباراة حية:", [m['home']['name'] + " vs " + m['away']['name'] for m in live], key="live_sel")
        if st.button("تحليل المباشر"):
            selected_match_id = live[[m['home']['name'] + " vs " + m['away']['name'] for m in live].index(choice)]['id']

with tab2:
    fixtures = get_matches("fixtures")
    if fixtures:
        choice_fix = st.selectbox("اختر مباراة قادمة:", [m['home']['name'] + " vs " + m['away']['name'] for m in fixtures], key="fix_sel")
        if st.button("تحليل القادمة"):
            selected_match_id = fixtures[[m['home']['name'] + " vs " + m['away']['name'] for m in fixtures].index(choice_fix)]['id']

# التحليل التنفيذي
if selected_match_id:
    with st.spinner('جاري التحليل...'):
        stats = get_match_stats(selected_match_id)
        if stats:
            st.write(analyze_betting_opportunities(stats))
        else:
            st.warning("لم يتم العثور على إحصائيات لهذه المباراة.")

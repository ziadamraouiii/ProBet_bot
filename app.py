import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", page_icon="📈", layout="wide")
st.title("📈 PENTAGON AI PRO - النظام الاحترافي المتكامل")

headers = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 1. جلب المباريات (Live + Upcoming)
def get_matches(status="live"):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/{status}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

# 2. جلب الإحصائيات المتقدمة (xG, Possession, etc)
def get_match_stats(match_id):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats?match_id={match_id}"
    response = requests.get(url, headers=headers)
    return response.json()

# 3. محرك التحليل الذكي (النموذج الهجين)
def analyze_betting_opportunities(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    
    prompt = f"""
    أنت محلل بيانات كروية خبير. حلل البيانات التالية: {str(stats_data)[:4000]}.
    1. قم بحساب احتمالات بويسون (Poisson Distribution) للأهداف بناءً على أرقام xG.
    2. قارن بين الاستحواذ، التسديدات على المرمى (xGOT)، والسيطرة الميدانية.
    3. اقترح رهانين أو ثلاثة (Betting Tips) تكون آمنة جداً (Odds > 1.50).
    4. اشرح السبب إحصائياً لكل رهان.
    """
    
    payload = {"model": "gpt-5.5", "input": prompt}
    response = requests.post(url, headers=headers_ai, json=payload)
    return response.json()['output'][0]['content'][0]['text']

# 4. واجهة المستخدم
tab1, tab2 = st.tabs(["🔴 مباريات مباشرة (LIVE)", "🗓️ مباريات قادمة (UPCOMING)"])

with tab1:
    live_matches = get_matches("live")
    # عرض المباريات واختيار واحدة... (نفس المنطق السابق)

with tab2:
    upcoming = get_matches("fixtures")
    # عرض المباريات...

# عند اختيار مباراة وتحليلها
if st.button("🚀 تنفيذ التحليل الهجين"):
    # جلب الإحصائيات + تحليل الذكاء الاصطناعي
    stats = get_match_stats(selected_match_id)
    analysis = analyze_betting_opportunities(stats)
    st.write(analysis)

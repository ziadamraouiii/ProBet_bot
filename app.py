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
    try:
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except:
        return []

# 2. جلب الإحصائيات
def get_match_stats(match_id):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats?match_id={match_id}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}

# 3. التحليل
def analyze_betting_opportunities(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    prompt = f"حلل البيانات التالية بدقة: {str(stats_data)}. اقترح رهانين أو ثلاثة آمنة (Odds > 1.5) مع تبرير إحصائي لكل رهان."
    response = requests.post(url, headers=headers_ai, json={"model": "gpt-5.5", "input": prompt})
    return response.json()['output'][0]['content'][0]['text'] if response.status_code == 200 else "خطأ في التحليل"

# 4. الواجهة (هنا كان الخلل)
tab1, tab2 = st.tabs(["🔴 مباريات مباشرة", "🗓️ مباريات قادمة"])

# دالة مساعدة لعرض القوائم
def display_matches(status):
    matches = get_matches(status)
    if not matches:
        st.write("لا توجد مباريات حالياً.")
        return None
    
    match_list = [m['home']['name'] + " vs " + m['away']['name'] for m in matches]
    choice = st.selectbox(f"اختر مباراة ({status}):", match_list, key=f"sel_{status}")
    
    if st.button(f"🚀 تحليل {status}", key=f"btn_{status}"):
        idx = match_list.index(choice)
        return matches[idx]['id']
    return None

with tab1:
    selected_id = display_matches("live")

with tab2:
    if not selected_id: # إذا لم يختر من live
        selected_id = display_matches("fixtures")

# تنفيذ التحليل النهائي
if selected_id:
    with st.spinner('جاري التحليل...'):
        stats = get_match_stats(selected_id)
        if stats:
            st.write(analyze_betting_opportunities(stats))
        else:
            st.warning("تعذر جلب إحصائيات هذه المباراة.")

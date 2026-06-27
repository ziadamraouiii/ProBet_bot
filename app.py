import streamlit as st
import requests

st.title("⚽ PENTAGON AI PRO - المرحلة النهائية")

HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 1. دالة جلب الإحصائيات (هنا نربط الـ ID بالبيانات)
def get_match_stats(match_id):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats"
    params = {"match_id": match_id}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json() if response.status_code == 200 else None

# 2. دالة التحليل الذكي (التي استخدمناها في البداية)
def analyze_betting(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    prompt = f"حلل بيانات المباراة التالية: {str(stats_data)}. اعطني رهانين آمنين (Odds > 1.5) مع التبرير."
    response = requests.post(url, headers=headers_ai, json={"model": "gpt-5.5", "input": prompt})
    return response.json()['output'][0]['content'][0]['text']

# --- هذا الجزء يربط ما اخترته أنت بالتحليل ---
# (استخدم نفس المنطق السابق للـ matches_map)
# ... [ضع هنا كود جلب المباريات من الرد السابق] ...

if st.button("تحليل المباراة المختارة"):
    # هنا يتم سحر الربط:
    match_id = matches_map[choice]
    with st.spinner('جاري سحب الإحصائيات من Flashscore...'):
        stats = get_match_stats(match_id)
        if stats:
            st.success("تم سحب البيانات! جاري التحليل...")
            final_report = analyze_betting(stats)
            st.write(final_report)
        else:
            st.error("لم نتمكن من الوصول لإحصائيات هذه المباراة، جرب مباراة أخرى.")

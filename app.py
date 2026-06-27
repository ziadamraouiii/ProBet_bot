import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", page_icon="🎯", layout="wide")
st.title("🎯 PENTAGON AI PRO - صياد الرهانات")

# دالة جلب المباريات الحية (بدل البحث بالـ ID)
def get_live_matches():
    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/live"
    headers = {
        "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
        "x-rapidapi-host": "flashscore4.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

# دالة التحليل الاستباقي (البرومبت المطور)
def get_pro_analysis(match_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    # البرومبت الجديد: "صياد الفرص"
    prompt = f"""
    أنت محلل رهانات محترف. حلل هذه المباراة: {str(match_data)[:3000]}.
    مهمتك:
    1. ابحث عن أي رهان (1X2, Over/Under, Handicap) تكون احتمالية حدوثه تتجاوز 75% بناءً على إحصائيات المباراة الحية.
    2. إذا وجدت رهانًا "قريب جداً للحدوث"، قم بتسليط الضوء عليه بوضوح مع ذكر السبب.
    3. لا تعطني تحليلات عامة، أريد اقتراحاً محدداً لرهان واحد قوي بناءً على الأداء اللحظي.
    """
    
    payload = {"model": "gpt-5.5", "input": prompt}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()['output'][0]['content'][0]['text'] if response.status_code == 200 else "خطأ في الاتصال"

# الواجهة
matches = get_live_matches()
if matches:
    match_names = [m['home']['name'] + " vs " + m['away']['name'] for m in matches]
    selected = st.selectbox("اختر مباراة حية لتحليلها:", match_names)
    
    if st.button("🚀 اقتنص الرهان الأقرب"):
        # جلب بيانات المباراة المختارة
        match_id = matches[match_names.index(selected)]['id']
        # جلب تفاصيل المباراة (نفس الـ Endpoint الذي استخدمته)
        match_details = requests.get(f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/point-by-point?match_id={match_id}", 
                                     headers={"x-rapidapi-key": st.secrets["RAPIDAPI_KEY"]}).json()
        
        analysis = get_pro_analysis(match_details)
        st.success("🎯 رهان الفرصة المقتنصة:")
        st.write(analysis)
else:
    st.write("لا توجد مباريات حية حالياً.")

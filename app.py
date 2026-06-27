import streamlit as st
import requests

st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="wide")
st.title("⚽ PENTAGON AI PRO - النظام الهجين")

# 1. جلب البيانات من الـ API الذي قدمته
def get_match_data(match_id):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/point-by-point"
    querystring = {"match_id": match_id}
    headers = {
        "x-rapidapi-key": "c1f2624c03mshfd0d4445263443dp1964a4jsna5852c4b9947",
        "x-rapidapi-host": "flashscore4.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response.json() if response.status_code == 200 else None

# 2. تحليل الذكاء الاصطناعي (النموذج الهجين)
def get_ai_analysis(match_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    # التعليمات الهجينة (Poisson + AI Context)
    prompt = f"""
    أنت خبير رهانات رياضية. حلل بيانات المباراة: {str(match_data)[:2000]}.
    مهمتك:
    1. قم بتطبيق منطق 'توزيع بويسون' (Poisson) لتقدير احتمالات الأهداف بناءً على النقاط المسجلة.
    2. ادمج ذلك مع الأداء اللحظي (Point by point).
    3. أعطني نتيجة واحدة (1X2 أو Over/Under) مع نسبة ثقة.
    """
    
    payload = {"model": "gpt-5.5", "input": prompt}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return str(data.get('output', data.get('content', '')))
    return "خطأ في الاتصال"

# 3. واجهة الاستخدام
match_id = st.text_input("📍 أدخل معرف المباراة (Match ID):", value="xp0yZYPr")

if st.button("🚀 بدء التحليل الهجين"):
    with st.spinner('جاري معالجة البيانات وبناء النموذج...'):
        data = get_match_data(match_id)
        if data:
            analysis = get_ai_analysis(data)
            st.success("✅ التحليل الاستراتيجي:")
            st.write(analysis)
        else:
            st.error("⚠️ فشل جلب البيانات. تأكد من الـ Match ID.")

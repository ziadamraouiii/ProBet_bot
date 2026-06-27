import streamlit as st
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="📈", layout="wide")
st.title("📈 PENTAGON AI PRO - النظام الاحترافي الشامل")

# إعدادات الـ API
HEADERS = {
    "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
    "x-rapidapi-host": "flashscore4.p.rapidapi.com"
}

# 2. الدوال الأساسية
def get_matches(endpoint):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_match_stats(match_id):
    url = f"https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/match/stats?match_id={match_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else {}

def analyze_betting(stats_data):
    url = "https://api.openmodel.ai/v1/responses"
    headers_ai = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    prompt = f"""
    أنت محلل رهانات محترف. حلل هذه البيانات: {str(stats_data)}.
    المطلوب:
    1. حساب احتمالات بويسون (Poisson) للأهداف.
    2. اقتراح 2-3 رهانات آمنة (Odds > 1.5) مع التبرير الإحصائي.
    3. التركيز على الاستدلال الرياضي وليس التوقعات العشوائية.
    """
    response = requests.post(url, headers=headers_ai, json={"model": "gpt-5.5", "input": prompt})
    return response.json()['output'][0]['content'][0]['text'] if response.status_code == 200 else "خطأ في الاتصال بالذكاء الاصطناعي."

# 3. الواجهة
tab1, tab2 = st.tabs(["🔴 مباريات مباشرة (Live)", "🗓️ مباريات قادمة (Fixtures)"])

def process_tab(status, tab_name):
    matches = get_matches(status)
    if not matches:
        st.write(f"لا توجد {tab_name} حالياً.")
        return None
    
    match_names = [f"{m['home']['name']} vs {m['away']['name']}" for m in matches]
    choice = st.selectbox(f"اختر مباراة من {tab_name}:", match_names, key=f"sel_{status}")
    
    if st.button(f"🚀 تحليل {tab_name}", key=f"btn_{status}"):
        idx = match_names.index(choice)
        return matches[idx]['id']
    return None

with tab1:
    selected_id = process_tab("live", "المباشر")
with tab2:
    if not selected_id:
        selected_id = process_tab("fixtures", "القادمة")

# 4. تنفيذ التحليل
if selected_id:
    with st.spinner('جاري جمع الإحصائيات وبناء النموذج...'):
        stats = get_match_stats(selected_id)
        if stats:
            analysis = analyze_betting(stats)
            st.success("✅ تحليل الفرصة المقتنصة:")
            st.write(analysis)
        else:
            st.error("لم نتمكن من جلب إحصائيات هذه المباراة.")

# رابط إضافي للتأكد من أن الـ API يعمل
st.sidebar.info("ملاحظة: إذا لم تظهر مباريات، جرب تحديث الصفحة لاحقاً.")

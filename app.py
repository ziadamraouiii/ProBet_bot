import streamlit as st
import pandas as pd
import sqlite3
import math
import requests
import json

# إعداد الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽")
st.title("⚽ PENTAGON AI PRO - وضع التشخيص")

# 1. قائمة الرهانات
MY_BETS = ["فوز المضيف (1)", "فوز الضيف (2)", "التعادل (X)", "أكثر من 2.5", "أقل من 2.5"]

# 2. دالة التشخيص (تُظهر لنا ما يحدث بالضبط)
def diagnose_api_connection():
    url = "https://api.openmodel.app/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "test"}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        st.write("---")
        st.write("🔍 **نتائج التشخيص:**")
        st.write(f"Status Code: {response.status_code}")
        st.json(response.json()) # هذا سيكشف لنا حقيقة الخطأ
        return response.status_code == 200
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return False

# 3. الواجهة
if st.button("🛠️ تشخيص الاتصال"):
    if diagnose_api_connection():
        st.success("✅ الاتصال يعمل! الآن يمكنك التحليل.")
    else:
        st.error("❌ فشل الاتصال. تحقق من الرد أعلاه.")

# 4. محرك التحليل (نسخة معدلة للتشخيص)
def get_ai_analysis(content):
    url = "https://api.openmodel.app/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": content}]}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"🚨 الخطأ: {response.status_code} | النص: {response.text}"

# (باقي كود التحليل كما هو سابقاً...)

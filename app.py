import streamlit as st
import pandas as pd
import sqlite3
import os
from openai import OpenAI

# إعداد العميل (سحب المفتاح من بيئة العمل)
api_key = os.getenv('DEEPSEEK_API_KEY')
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def get_ai_analysis(stats_summary):
    prompt = f"""
    أنت خبير في تحليل المراهنات الرياضية. قم بتحليل هذه البيانات لآخر المباريات:
    {stats_summary}
    بناءً على المعطيات، قدم لي:
    1. أفضل رهان (من بين 10 خيارات شائعة).
    2. نسبة الثقة في هذا الرهان.
    3. مبررات منطقية مختصرة.
    أجب باللغة العربية.
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ... (باقي كود جلب البيانات من القاعدة كما هو) ...

if st.button("تحليل المباراة بواسطة الذكاء الاصطناعي"):
    # تجهيز البيانات
    stats_summary = match_info.to_string()
    
    with st.spinner('جاري التحليل بواسطة DeepSeek...'):
        analysis = get_ai_analysis(stats_summary)
        st.markdown("### 🤖 توصية المحلل الذكي:")
        st.info(analysis)

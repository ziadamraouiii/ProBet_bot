import streamlit as st
import pandas as pd
import sqlite3
import math
from openai import OpenAI
import os

# إعدادات الصفحة
st.set_page_config(page_title="PENTAGON AI PRO", layout="centered")
st.title("⚽ PENTAGON AI PRO")

# جلب البيانات
def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# محرك بويسون
def poisson_prob(x, mu):
    return (math.exp(-mu) * (mu**x)) / math.factorial(x)

# التحليل
if st.button("🚀 تحليل المباراة"):
    # 1. جلب البيانات أولاً
    query = "SELECT * FROM cached_matches WHERE tournament_name = ? AND ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))"
    match_info = get_db_data(query, (selected_league, home_team, away_team, away_team, home_team))
    
    # 2. التأكد من وجود بيانات قبل أي شيء
    if not match_info.empty:
        st.success("✅ تم العثور على بيانات!")
        
        # حسابات بويسون (بسيطة ومباشرة)
        stats_summary = match_info.to_string()
        
        # 3. الاتصال بالـ API داخل Try/Except
        try:
            client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"حلل التالي: {stats_summary}"}]
            )
            st.write(response.choices[0].message.content)
        except Exception as e:
            st.error(f"خطأ في الاتصال بالذكاء الاصطناعي: {e}")
    else:
        st.warning("⚠️ لا توجد بيانات للمباراة.")
            WHERE tournament_name = ? AND 
            (home_team IN (?, ?) OR away_team IN (?, ?))
            """
            df = get_db_data(query, (selected_league, home_team, away_team, home_team, away_team))
            
            if not df.empty:
                # تحويل الأهداف إلى أرقام
                df['home_score'] = pd.to_numeric(df['home_score'], errors='coerce').fillna(0)
                df['away_score'] = pd.to_numeric(df['away_score'], errors='coerce').fillna(0)
                
                # حساب متوسط الأهداف (كبديل للـ xG)
                home_xg = df[df['home_team'] == home_team]['home_score'].mean()
                if pd.isna(home_xg) or home_xg == 0: home_xg = 1.2 # قيمة افتراضية إذا لم تتوفر بيانات كافية
                
                away_xg = df[df['away_team'] == away_team]['away_score'].mean()
                if pd.isna(away_xg) or away_xg == 0: away_xg = 1.0

                # تشغيل محرك بويسون الرياضي
                hw, d, aw, o25, btts = calculate_match_probabilities(home_xg, away_xg)
                probs = {'home_win': hw, 'draw': d, 'away_win': aw, 'over_2_5': o25, 'btts': btts}

                st.success("✅ تمت معالجة البيانات بنجاح!")
                
                # عرض الأرقام بشكل احترافي
                st.markdown("### 📊 التحليل الرياضي (توزيع بويسون)")
                m1, m2, m3 = st.columns(3)
                m1.metric(f"فوز {home_team}", f"{hw:.1%}")
                m2.metric("التعادل", f"{d:.1%}")
                m3.metric(f"فوز {away_team}", f"{aw:.1%}")
                
                m4, m5 = st.columns(2)
                m4.metric("أكثر من 2.5 أهداف (Over 2.5)", f"{o25:.1%}")
                m5.metric("كلا الفريقين يسجل (BTTS)", f"{btts:.1%}")
                
                st.markdown("---")
                
                # تشغيل المحلل الذكي
                with st.spinner('🤖 DeepSeek يقوم بتحليل الأرقام وصياغة أفضل رهان...'):
                    ai_recommendation = get_ai_analysis(home_team, away_team, df.head(10).to_string(), probs)
                    st.markdown("### 💎 القرار النهائي (توصية المحلل الذكي):")
                    st.info(ai_recommendation)
            else:
                st.warning("⚠️ لا توجد بيانات كافية في قاعدة البيانات لحساب التوقعات لهذه الفرق.")
else:
    st.info("⏳ جاري انتظار تحميل قاعدة البيانات من GitHub...")

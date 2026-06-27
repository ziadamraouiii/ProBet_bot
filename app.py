import streamlit as st
import pandas as pd
import sqlite3
import os
import math
from openai import OpenAI

# ==========================================
# 1. إعدادات التطبيق والذكاء الاصطناعي
# ==========================================
st.set_page_config(page_title="PENTAGON AI PRO", page_icon="⚽", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>⚽ PENTAGON AI PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>المحرك الذكي لتحليل المباريات وتوقعات بويسون</p>", unsafe_allow_html=True)
st.markdown("---")

api_key = st.secrets.get("DEEPSEEK_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ==========================================
# 2. دوال قواعد البيانات والرياضيات
# ==========================================
def get_db_data(query, params=()):
    conn = sqlite3.connect('analytics_v6.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def poisson_probability(actual_goals, expected_goals):
    """حساب احتمالية تسجيل عدد معين من الأهداف بناءً على بويسون"""
    return ((expected_goals ** actual_goals) * math.exp(-expected_goals)) / math.factorial(actual_goals)

def calculate_match_probabilities(home_xg, away_xg):
    """محاكاة المباراة لحساب نسب الفوز والتعادل والأهداف"""
    home_win, draw, away_win, over_2_5, btts = 0.0, 0.0, 0.0, 0.0, 0.0
    
    # محاكاة لنتائج من 0 إلى 5 أهداف لكل فريق
    for i in range(6):
        for j in range(6):
            prob = poisson_probability(i, home_xg) * poisson_probability(j, away_xg)
            if i > j: home_win += prob
            elif i == j: draw += prob
            else: away_win += prob
            
            if (i + j) > 2.5: over_2_5 += prob
            if i > 0 and j > 0: btts += prob
            
    return home_win, draw, away_win, over_2_5, btts

def get_ai_analysis(home, away, stats_df, probabilities):
    """إرسال الأرقام الجاهزة للذكاء الاصطناعي لاستخراج الرهان"""
    prompt = f"""
    أنت خبير مراهنات رياضي محترف.
    المباراة: {home} ضد {away}.
    
    حسابات توزيع بويسون الدقيقة لهذه المباراة أعطت الاحتمالات التالية:
    - فوز المضيف ({home}): {probabilities['home_win']:.1%}
    - التعادل: {probabilities['draw']:.1%}
    - فوز الضيف ({away}): {probabilities['away_win']:.1%}
    - احتمالية أهداف Over 2.5: {probabilities['over_2_5']:.1%}
    - احتمالية تسجيل الفريقين (BTTS): {probabilities['btts']:.1%}
    
    بناءً على هذه الاحتمالات الرياضية الدقيقة، والإحصائيات العامة:
    {stats_df}
    
    أعطني حصرياً:
    1. "أفضل رهان" (الأكثر أماناً وربحية).
    2. نسبة الثقة في هذا الرهان.
    3. تحليل تكتيكي سريع يبرر هذا الاختيار.
    أجب باللغة العربية بأسلوب احترافي ومباشر.
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3 # تقليل العشوائية ليكون الرد دقيقاً ومنطقياً
    )
    return response.choices[0].message.content

# ==========================================
# 3. واجهة المستخدم والتفاعل
# ==========================================
try:
    leagues_df = get_db_data("SELECT DISTINCT tournament_name FROM cached_matches")
    leagues = leagues_df['tournament_name'].tolist()
except:
    leagues = []

if leagues:
    selected_league = st.selectbox("🏆 اختر الدوري:", leagues)
    
    teams_query = """
    SELECT DISTINCT home_team FROM cached_matches WHERE tournament_name = ? 
    UNION 
    SELECT DISTINCT away_team FROM cached_matches WHERE tournament_name = ?
    """
    teams = sorted(get_db_data(teams_query, (selected_league, selected_league)).iloc[:, 0].tolist())
    
    col1, col2 = st.columns(2)
    home_team = col1.selectbox("🏠 الفريق المضيف", teams)
    away_team = col2.selectbox("✈️ الفريق الضيف", teams)

    if st.button("🚀 تشغيل محرك التحليل الشامل (Poisson + AI)", use_container_width=True):
        if home_team == away_team:
            st.error("⚠️ يرجى اختيار فريقين مختلفين!")
        else:
            # جلب مباريات الفريقين لتقدير القوة الهجومية والدفاعية
            query = """
            SELECT home_team, away_team, home_score, away_score 
            FROM cached_matches 
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

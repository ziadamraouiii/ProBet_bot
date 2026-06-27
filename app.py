import streamlit as st

def calculate_stats_engine(home_wins, home_draws, home_losses, away_wins, away_draws, away_losses):
    # معادلة حساب القوة (Points / Total Games)
    home_score = (home_wins * 3 + home_draws * 1) / 5
    away_score = (away_wins * 3 + away_draws * 1) / 5
    
    total = home_score + away_score
    
    # تحويل القوة إلى نسب مئوية (كما في الصورة)
    home_prob = round((home_score / total) * 100)
    away_prob = round((away_score / total) * 100)
    draw_prob = 100 - (home_prob + away_prob)
    
    return home_prob, away_prob, draw_prob

st.title("📊 محرك التوقعات الرياضية (النسخة الإحصائية)")

# مدخلات يدوية (يمكننا ربطها لاحقاً بالسحب المباشر)
home_name = st.text_input("اسم فريق الأرض:", "Carlos Mannucci")
h_w = st.number_input("فوز الأرض:", 0, 5, 2)
h_d = st.number_input("تعادل الأرض:", 0, 5, 1)
h_l = st.number_input("خسارة الأرض:", 0, 5, 2)

away_name = st.text_input("اسم فريق الضيف:", "Llacuabamba")
a_w = st.number_input("فوز الضيف:", 0, 5, 1)
a_d = st.number_input("تعادل الضيف:", 0, 5, 1)
a_l = st.number_input("خسارة الضيف:", 0, 5, 3)

if st.button("احسب الاحتمالات"):
    h_p, a_p, d_p = calculate_stats_engine(h_w, h_d, h_l, a_w, a_d, a_l)
    
    # عرض النتائج كأشرطة بيانية (مثل الصورة)
    st.write(f"### {home_name} vs {away_name}")
    st.write(f"فوز {home_name}: {h_p}%")
    st.progress(h_p / 100)
    
    st.write(f"تعادل: {d_p}%")
    st.progress(d_p / 100)
    
    st.write(f"فوز {away_name}: {a_p}%")
    st.progress(a_p / 100)

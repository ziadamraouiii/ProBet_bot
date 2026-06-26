import sqlite3

def get_team_data(team_name):
    conn = sqlite3.connect("analytics_v6.db")
    c = conn.cursor()
    # جلب آخر 10 مباريات للفريق
    c.execute("""SELECT home_score, away_score FROM cached_matches 
                 WHERE home_team = ? OR away_team = ? 
                 ORDER BY match_date DESC LIMIT 10""", (team_name, team_name))
    rows = c.fetchall()
    conn.close()
    
    # تحويل البيانات إلى تنسيق (سجل، استقبل)
    stats = []
    for h_sc, a_sc in rows:
        # إذا كان الفريق هو المضيف، نأخذ home_score و away_score
        # هذه الدالة تحتاج تنسيق بسيط حسب مسمياتك
        stats.append((h_sc, a_sc))
    return stats

def get_team_stats_clean(team_name):
    conn = sqlite3.connect("analytics_v6.db")
    c = conn.cursor()
    c.execute("""SELECT home_team, away_team, home_score, away_score 
                 FROM cached_matches 
                 WHERE home_team = ? OR away_team = ? 
                 ORDER BY match_date DESC LIMIT 10""", (team_name, team_name))
    rows = c.fetchall()
    conn.close()
    
    stats = []
    for home_team, away_team, h_sc, a_sc in rows:
        if home_team == team_name:
            # الفريق هو المضيف
            stats.append({'scored': h_sc, 'conceded': a_sc})
        else:
            # الفريق هو الضيف
            stats.append({'scored': a_sc, 'conceded': h_sc})
    return stats

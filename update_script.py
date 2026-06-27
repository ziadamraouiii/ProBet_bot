import requests
import sqlite3
import os

API_KEY = os.getenv('API_KEY')
LEAGUES = [2021, 2003, 2001] # أضف أي دوري تريده هنا
DB_NAME = 'analytics_v6.db'

def update_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    headers = {'X-Auth-Token': API_KEY}
    
    for league_id in LEAGUES:
        url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            matches = response.json().get('matches', [])
            for match in matches:
                # هذا الجزء يحدث الجدول بناءً على البيانات القادمة من الـ API
                cursor.execute('''
                    INSERT OR REPLACE INTO cached_matches 
                    (home_team, away_team, home_score, away_score, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    match['homeTeam']['name'],
                    match['awayTeam']['name'],
                    match['score']['fullTime']['home'],
                    match['score']['fullTime']['away'],
                    match['status']
                ))
            print(f"تم تحديث الدوري {league_id} بنجاح.")
        else:
            print(f"فشل الدوري {league_id}: {response.status_code}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_database()

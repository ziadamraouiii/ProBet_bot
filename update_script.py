import requests
import sqlite3
import os

# جلب المفتاح الذي حفظناه في Secrets
API_KEY = os.getenv('API_KEY') 
LEAGUES = [2021, 2003, 2001] # أضف أكواد الدوريات التي تريدها هنا

def update_database():
    conn = sqlite3.connect('analytics_v6.db')
    headers = {'X-Auth-Token': API_KEY}
    
    for league_id in LEAGUES:
        url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # هنا نقوم بمعالجة البيانات وتحديث جدول cached_matches
                # يمكنك استخدام pandas لعمل dataframe ثم تحويله للـ DB
                print(f"تم جلب بيانات الدوري: {league_id}")
            else:
                print(f"فشل جلب الدوري {league_id}: {response.status_code}")
        except Exception as e:
            print(f"خطأ: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_database()


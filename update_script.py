# قائمة شاملة لجميع الدوريات المتاحة في الـ API
LEAGUES = [2013, 2016, 2021, 2001, 2018, 2015, 2002, 2019, 2003, 2017, 2152, 2014, 2000]

def update_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # تحذير: إذا كانت قاعدة البيانات كبيرة، قد يستغرق هذا وقتاً أطول قليلاً
    # لذا سنقوم بمسح البيانات القديمة لضمان تحديثها بكل الدوريات الجديدة
    cursor.execute('DELETE FROM cached_matches')
    
    headers = {'X-Auth-Token': API_KEY}
    
    for league_id in LEAGUES:
        url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                matches = response.json().get('matches', [])
                for match in matches:
                    cursor.execute('''
                        INSERT OR REPLACE INTO cached_matches 
                        (home_team, away_team, home_score, away_score, status, tournament_name)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        match['homeTeam']['name'],
                        match['awayTeam']['name'],
                        str(match['score']['fullTime']['home']),
                        str(match['score']['fullTime']['away']),
                        match['status'],
                        match['competition']['name'] # تخزين اسم الدوري للفلترة لاحقاً
                    ))
                print(f"تمت إضافة الدوري رقم {league_id} بنجاح.")
        except Exception as e:
            print(f"خطأ أثناء تحديث الدوري {league_id}: {e}")
            
    conn.commit()
    conn.close()

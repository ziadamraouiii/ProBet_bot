import sqlite3

def update_db_schema():
    conn = sqlite3.connect("analytics_v6.db")
    c = conn.cursor()
    
    # 1. حذف الجدول القديم (تأكد من الاحتفاظ بنسخة إذا كنت تحتاج البيانات)
    c.execute("DROP TABLE IF EXISTS cached_matches")
    
    # 2. إنشاء جدول جديد بهيكل أكثر دقة
    c.execute('''CREATE TABLE cached_matches 
                 (match_date TEXT, 
                  league_id INTEGER, 
                  home_team TEXT, 
                  away_team TEXT, 
                  home_score INTEGER, 
                  away_score INTEGER,
                  is_finished INTEGER)''') # إضافة حالة المباراة
    
    conn.commit()
    conn.close()
    print("تم تحديث هيكل قاعدة البيانات بنجاح.")

update_db_schema()


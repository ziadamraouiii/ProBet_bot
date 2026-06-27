# سكربت بسيط لمعرفة الـ ID لأي دوري
import requests
headers = {'X-Auth-Token': 'YOUR_API_KEY'}
response = requests.get("https://api.football-data.org/v4/competitions", headers=headers)
for comp in response.json()['competitions']:
    print(f"اسم الدوري: {comp['name']}, الـ ID الخاص به: {comp['id']}")


import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv('ERC_EMAIL')
PASSWORD = os.getenv('ERC_PASSWORD')
API_URL = 'https://connect.erc.ua/connectservice/api/specprice/DoExport'

def sync_data():
    payload = {
        "Email": EMAIL,
        "Pass": PASSWORD,
        "Infotype": 6,
        "IsJson": True,
        "lang": "ua",
        "OnlyFree": 1
    }
    
    print("🔄 Запит до API...")
    try:
        r = requests.post(API_URL, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            
            # Очищаємо значення quantity (">50" -> 50)
            if isinstance(data, list):
                for item in data:
                    if 'whs' in item and isinstance(item['whs'], list):
                        for wh in item['whs']:
                            if 'q' in wh and isinstance(wh['q'], str) and '>' in wh['q']:
                                wh['q'] = wh['q'].replace('>', '')
            
            # Зберігаємо
            with open('erc_products.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            count = len(data) if isinstance(data, list) else len(data.get('goods', []))
            print(f"✅ Збережено {count} товарів")
            
            # Бекап
            os.makedirs('backups', exist_ok=True)
            backup_name = f"backups/erc_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Бекап: {backup_name}")
            
        else:
            print(f"❌ HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    sync_data()
import requests
import json
import os
from datetime import datetime

# Отримуємо дані з секретів GitHub Actions (або використовуємо значення за замовчуванням)
EMAIL = os.environ.get('ERC_EMAIL', 'rozd32@gmail.com')
PASSWORD = os.environ.get('ERC_PASSWORD', '159159')
API_URL = "https://connect.erc.ua/connectservice/api/specprice/DoExport"

def sync_data():
    print(f"[{datetime.now()}] Запуск синхронізації...")
    
    payload = {
        "Email": EMAIL,
        "Pass": PASSWORD,
        "Infotype": 6,
        "IsJson": True,
        "lang": "ua",
        "OnlyFree": 1
    }
    
    try:
        print("📡 Надсилаю запит до API...")
        r = requests.post(API_URL, json=payload, timeout=60)
        print(f"📊 HTTP статус: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            
            # Очищаємо значення quantity (">50" -> 50)
            if isinstance(data, list):
                for item in data:
                    if 'whs' in item and isinstance(item['whs'], list):
                        for wh in item['whs']:
                            if 'q' in wh and isinstance(wh['q'], str) and '>' in wh['q']:
                                wh['q'] = wh['q'].replace('>', '')
            
            # Зберігаємо файл
            with open('erc_products.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            count = len(data) if isinstance(data, list) else len(data.get('goods', []))
            print(f"✅ УСПІХ! Отримано {count} товарів")
            return True
        else:
            print(f"❌ HTTP помилка: {r.status_code}")
            print(f"Відповідь сервера: {r.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ КРИТИЧНА ПОМИЛКА: {e}")
        return False

if __name__ == "__main__":
    success = sync_data()
    exit(0 if success else 1)

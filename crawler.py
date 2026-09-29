import json
import requests

def debug_crawler():
    api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"
    payload = {
        "Page": 1,
        "PageSize": 10  # 先抓 10 筆就好
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Referer": "https://course.taiwanjobs.gov.tw/"
    }

    response = requests.post(api_url, json=payload, headers=headers, timeout=15)
    if response.status_code == 200:
        rows = response.json().get("rows", [])
        print(f"API 成功回傳 {len(rows)} 筆資料。前 3 筆的 TrainingUnit 分別為：")
        for idx, item in enumerate(rows[:3]):
            print(f"[{idx+1}] TrainingUnit 內容: '{item.get('TrainingUnit')}' | 課程名稱: {item.get('Name')}")
    else:
        print("API 請求失敗")

if __name__ == "__main__":
    debug_crawler()

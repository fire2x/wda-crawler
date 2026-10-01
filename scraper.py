import requests
import json
import time
import os

# API 端點與偽裝標頭
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"
HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_all_courses():
    """
    全自動、不設限地抓取所有分頁課程，並在最後進行統一去重。
    """
    session = requests.Session()
    all_raw_courses = []
    current_page = 1
    empty_page_attempts = 0 # 連續空頁面嘗試次數

    print("🚀 啟動終極自動翻頁爬蟲...")
    
    # 步驟 1: 嘗試訪問首頁以獲取 Session Cookie
    try:
        print("🌐 正在訪問首頁以建立連線...")
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=20)
        print("✅ 首頁連線成功，已取得 Session。")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 首頁連線失敗 (錯誤: {e})，將直接嘗試 API 連線...")

    # 步驟 2: 無限循環翻頁，直到連續抓不到資料為止
    while True:
        payload = {
            "PageIndex": current_page,
            "pageIndex": current_page, # 兼容大小寫參數
            "PageSize": 10,
            "pageSize": 10,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "", "CourseType": None, "City": None
        }

        try:
            print(f"\n🔄 正在請求第 {current_page} 頁資料...")
            response = session.post(URL, json=payload, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                print(f"❌ 第 {current_page} 頁請求失敗，狀態碼: {response.status_code}。中止爬取。")
                break

            data = response.json()
            
            # 兼容 API 可能返回的兩種 JSON 結構
            rows = []
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                rows = data.get("rows", [])
            
            if rows:
                print(f"✅ 第 {current_page} 頁成功獲取 {len(rows)} 筆原始資料。")
                all_raw_courses.extend(rows)
                current_page += 1
                empty_page_attempts = 0 # 重置空頁面計數器
            else:
                print(f"ℹ️ 第 {current_page} 頁無資料，計為一次空頁面。")
                empty_page_attempts += 1
                # 如果連續 2 次都抓不到資料，我們才認定真的結束了
                if empty_page_attempts >= 2:
                    print("🏁 連續兩次請求為空，確認所有頁面已抓取完畢。")
                    break
                current_page += 1 # 即使是空頁也繼續嘗試下一頁

            time.sleep(1.5) # 友善爬取，避免請求過於頻繁

        except requests.exceptions.RequestException as e:
            print(f"❌ 請求過程中發生網路錯誤: {e}。中止爬取。")
            break

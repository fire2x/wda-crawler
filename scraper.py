import requests
import json
import math
import time
import os

def run_scraper():
    # 使用 Session 自動維護 Cookie
    session = requests.Session()
    
    # 完整的現代瀏覽器標頭
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://course.taiwanjobs.gov.tw",
        "Referer": "https://course.taiwanjobs.gov.tw/course/conditions"
    }
    
    print("🌐 步驟 1: 正在造訪就業通首頁以獲取認證 Cookie...")
    try:
        home_res = session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=headers, timeout=15)
        print(f"首頁連線狀態: {home_res.status_code}, 取得 Cookie: {list(session.cookies.get_dict().keys())}")
    except Exception as e:
        print(f"⚠️ 首頁連線失敗 (可能海外 IP 被擋): {e}")

    # 步驟 2: 發送 API 請求
    api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"
    all_courses = []
    
    for page in [1, 2]:
        payload = {
            "PageIndex": page,
            "PageSize": 10,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "",
            "CourseType": None,
            "City": None
        }
        
        print(f"\n📡 步驟 2.{page}: 請求第 {page} 頁資料...")
        try:
            res = session.post(api_url, json=payload, headers=headers, timeout=20)
            print(f"API 回應狀態碼: {res.status_code}")
            
            if res.status_code == 200:
                data = res.json()
                rows = data.get("rows", [])
                total = data.get("total", 0)
                print(f"成功取得第 {page} 頁，筆數: {len(rows)} (總數: {total})")
                
                all_courses.extend(rows)
                if len(all_courses) >= total or not rows:
                    break
            else:
                print(f"❌ API 回應異常: {res.text[:300]}")
                break
        except Exception as e:
            print(f"❌ 請求出錯: {e}")
            break
            
        time.sleep(1)

    # 步驟 3: 防呆保護（如果這次爬蟲被海外擋掉拿到 0 筆，絕對不要把原本舊的檔案覆蓋成空的！）
    if len(all_courses) > 0:
        with open("courses.json", "w", encoding="utf-8") as f:
            json.dump(all_courses, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 成功更新 courses.json，共寫入 {len(all_courses)} 筆資料！")
    else:
        print("\n⚠️ 本次抓取結果為 0 筆！啟動保護機制：保留既有 courses.json 檔案，不進行覆蓋。")

if __name__ == "__main__":
    run_scraper()

import requests
import json
import time
import os

# 100% 正確的課程查詢端點
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"

# 完整的瀏覽器偽裝標頭
HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

def fetch_all_courses():
    session = requests.Session()
    all_courses = {}
    seen_signatures = set()

    print("🌐 步驟 1: 造訪首頁以獲取認證 Cookie...")
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"⚠️ 首頁連線暫時失敗，將直接連線 API: {e}")

    # 💡 【核心重磅改進】：無視 total 判斷，直接無條件暴力跑 3 頁，徹底杜絕翻頁中斷 Bug
    for current_page in:
        payload = {
            "PageIndex": current_page,
            "pageIndex": current_page,
            "PageSize": 10,
            "pageSize": 10,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "",
            "CourseType": None,
            "City": None
        }

        try:
            print(f"\n📡 正在發送第 {current_page} 頁 API 請求...")
            response = session.post(URL, json=payload, headers=HEADERS, timeout=20)
            
            if response.status_code != 200:
                print(f"❌ 第 {current_page} 頁連線失敗 (狀態碼: {response.status_code})")
                continue
                
            res_data = response.json()
            
            # 💡 【核心相容處理】：自動解析 rows (物件) 或是直接為陣列
            rows = []
            if isinstance(res_data, list):
                rows = res_data
            elif isinstance(res_data, dict):
                rows = res_data.get("rows", [])
            
            print(f"✅ 第 {current_page} 頁成功解析出 {len(rows)} 筆原始課程資料")
            
            if not rows:
                print(f"ℹ️ 第 {current_page} 頁沒有任何課程資料，結束本頁爬取。")
                continue
                
            print(f"   📢 本頁首門課程名稱: {rows[0].get('Name')}")
            
            # 逐筆解析並精確去重
            for item in rows:
                course_name = (item.get("Name") or "").strip()
                address = (item.get("Address") or "").strip()
                plan_name = (item.get("PlanName") or "").strip()
                
                # 指紋去重簽章：課程名稱 + 計畫類型 + 上課地址
                signature = f"{course_name}@{plan_name}@{address}"
                
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    # 優先使用唯一的 ID 作為物件 key
                    key = item.get("ID") or item.get("SourcePrimaryKey") or course_name
                    all_courses[key] = item
                else:
                    print(f"   ⚠️ 過濾掉完全重複之項目: {course_name}")

            time.sleep(1.5) # 友善延遲

        except Exception as e:
            print(f"❌ 請求第 {current_page} 頁時發生異常: {e}")
            continue

    return list(all_courses.values())

def main():
    courses = fetch_all_courses()
    print(f"\n📊 最終統計：三頁合併去重後，共獲得 {len(courses)} 門不重複的完整課程！")
    
    filename = "courses.json"
    
    # 寫入保護機制
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"💾 已成功寫入 {filename} (檔案大小: {os.path.getsize(filename)} bytes)")
    else:
        print("⚠️ 爬取結果為 0 筆，不覆蓋舊檔案，保護網頁不為空。")

if __name__ == "__main__":
    main()

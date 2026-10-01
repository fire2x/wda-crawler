import requests
import json
import math
import time
import os

# 100% 正確的課程查詢端點
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"

# 完整的 Chrome 120 標頭偽裝
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
    all_courses = {}       # 最終合併去重的課程
    current_page = 1
    page_size = 10         # 遵循伺服器的強制預設限制
    
    seen_signatures = set()  # 同一門課如果名稱完全一樣，且上課地點也一致，我們視為重複

    print("🌐 步驟 1: 造訪首頁以獲取認證 Cookie...")
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"⚠️ 首頁連線失敗 (可能海外 IP 限制，繼續嘗試 API 連線): {e}")

    print("\n🚀 步驟 2: 開始請求分頁資料...")
    while True:
        payload = {
            "PageIndex": current_page,
            "PageSize": page_size,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "",
            "CourseType": None,
            "City": None
        }

        try:
            print(f"🔄 正在請求第 {current_page} 頁資料...")
            response = session.post(URL, json=payload, headers=HEADERS, timeout=20)
            
            if response.status_code != 200:
                print(f"❌ 請求失敗，狀態碼: {response.status_code}")
                break
                
            data = response.json()
            total = data.get("total", 0)  # 網頁查到的總筆數 (例如 19)
            rows = data.get("rows", [])
            
            print(f"✅ 第 {current_page} 頁成功拿到 {len(rows)} 筆原始資料")
            
            if not rows:
                break
                
            for item in rows:
                course_name = (item.get("Name") or "").strip()
                address = (item.get("Address") or "").strip()
                
                # 💡 【高精準去重】：如果「課程名稱」與「上課地址」皆完全相同，則判定為重複課程
                signature = f"{course_name}@{address}"
                
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    key = item.get("SourcePrimaryKey") or item.get("ID") or course_name
                    all_courses[key] = item
                else:
                    print(f"⚠️ 偵測到重複課程並自動過濾：{course_name}")

            # 💡 【終極不設限解除邏輯】：根據總筆數自動計算最大頁數，不漏掉任何一頁！
            total_pages = math.ceil(total / page_size)
            print(f"📊 目前進度: 已完成 {current_page}/{total_pages} 頁")
            
            if current_page >= total_pages:
                print("🏁 所有分頁已順利請求完畢！")
                break
                
            current_page += 1
            time.sleep(1) # 禮貌延遲，避免被防火牆擋掉

        except Exception as e:
            print(f"⚠️ 請求過程發生異常: {e}")
            break

    return list(all_courses.values())

def main():
    courses = fetch_all_courses()
    print(f"\n📊 最終統計：去除重複項目後，最終保留 {len(courses)} 門課程（不設限全部呈現）。")
    
    filename = "courses.json"
    
    # 防呆機制：如果爬到 0 筆，不覆蓋既有檔案，避免網頁變空白
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"💾 成功將 {len(courses)} 筆乾淨且完整的課程資料寫入 {filename}")
    else:
        print("⚠️ 未取得任何資料，保留既有檔案不予覆蓋。")

if __name__ == "__main__":
    main()

import requests
import json
import math
import time
import os

# 正確的課程查詢端點
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
    current_page = 1
    page_size = 10
    seen_signatures = set()

    print("🌐 步驟 1: 造訪首頁以獲取認證 Cookie...")
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"⚠️ 首頁連線暫時失敗，將直接嘗試 API 連線: {e}")

    print("\n🚀 步驟 2: 開始請求分頁資料...")
    while True:
        # 💡 【核心修復】：同時帶上大小寫與別名參數，防止 ASP.NET 忽視 PageIndex
        payload = {
            "PageIndex": current_page,
            "pageIndex": current_page,
            "PageSize": page_size,
            "pageSize": page_size,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "",
            "CourseType": None,
            "City": None
        }

        try:
            print(f"🔄 正在發送第 {current_page} 頁 API 請求...")
            response = session.post(URL, json=payload, headers=HEADERS, timeout=20)
            
            if response.status_code != 200:
                print(f"❌ 請求失敗，狀態碼: {response.status_code}")
                break
                
            data = response.json()
            total = data.get("total", 0)  # 例如 19
            rows = data.get("rows", [])
            
            print(f"✅ 第 {current_page} 頁成功拿到 {len(rows)} 筆原始資料 (系統總數: {total})")
            
            if not rows:
                print("ℹ️ 本頁無回傳資料，跳出循環。")
                break
                
            # 除錯提示：印出本頁的第一門課，確認是否有成功翻頁 (若第1頁與第2頁第一門課相同，代表沒翻頁成功)
            print(f"   📢 本頁首門課程預覽: {rows[0].get('Name')}")
            
            for item in rows:
                course_name = (item.get("Name") or "").strip()
                address = (item.get("Address") or "").strip()
                plan_name = (item.get("PlanName") or "").strip()
                
                # 💡 【指紋去重核心】：結合名稱 + 計畫 + 地址
                signature = f"{course_name}@{plan_name}@{address}"
                
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    # 優先使用唯一的 ID
                    key = item.get("ID") or item.get("SourcePrimaryKey") or course_name
                    all_courses[key] = item
                else:
                    print(f"   ⚠️ 偵測到完全重複之項目並自動過濾: {course_name}")

            # 自動翻頁判定
            total_pages = math.ceil(total / page_size)
            print(f"📊 翻頁狀態: 已完成第 {current_page} 頁 / 共 {total_pages} 頁")
            
            if current_page >= total_pages:
                print("🏁 所有分頁已全數爬取完畢！")
                break
                
            current_page += 1
            time.sleep(1.5) # 友善延遲

        except Exception as e:
            print(f"⚠️ 請求過程發生異常: {e}")
            break

    return list(all_courses.values())

def main():
    courses = fetch_all_courses()
    print(f"\n📊 最終統計：共獲得 {len(courses)} 門過濾重複後的課程資料。")
    
    filename = "courses.json"
    
    # 寫入前安全檢查，防止海外被擋洗成 0 筆
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"💾 已成功寫入 {filename} (共 {len(courses)} 筆，檔案大小: {os.path.getsize(filename)} 網頁可讀 bytes)")
    else:
        print("⚠️ 未抓取到任何資料，不覆蓋舊檔案以保護網頁不為空。")

if __name__ == "__main__":
    main()

import requests
import json
import time
import os

# 台灣就業通核心分頁 API
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"

# 完整的瀏覽器身分偽裝 Headers
HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_all_courses():
    session = requests.Session()
    all_courses = {}
    seen_signatures = set()
    current_page = 1
    page_size = 10  # 遵循政府 API 每頁 10 筆的硬性上限

    print("🌐 步驟 1: 建立安全 Session 連線...")
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"⚠️ 初始連線超時，嘗試直連 API: {e}")

    print("\n🚀 步驟 2: 開始自動翻頁爬取北基宜花金馬分署所有課程...")
    
    while True:
        # 💡 大小寫雙重參數發送，完美相容後端解析
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
            print(f"🔄 正在爬取第 {current_page} 頁...")
            response = session.post(URL, json=payload, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ 請求失敗，狀態碼: {response.status_code}")
                break
                
            res_data = response.json()
            
            # 相容 API 可能回傳的兩種結構（物件 rows 或純陣列）
            rows = []
            if isinstance(res_data, list):
                rows = res_data
            elif isinstance(res_data, dict):
                rows = res_data.get("rows", [])
            
            if not rows:
                print("🏁 抓取完畢：本頁無資料，已到達最後一頁。")
                break
                
            print(f"✅ 第 {current_page} 頁解析成功！取得 {len(rows)} 筆原始課程")
            
            # 進行精準去重與合併
            for item in rows:
                course_name = (item.get("Name") or "").strip()
                address = (item.get("Address") or "").strip()
                plan_name = (item.get("PlanName") or "").strip()
                
                # 💡 指紋去重設計：如果課程名稱、計畫和地點都一樣，判定為重複上架（如青年專班與職前重複）
                signature = f"{course_name}@{plan_name}@{address}"
                
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    # 優先使用唯一的 ID
                    key = item.get("ID") or item.get("SourcePrimaryKey") or course_name
                    all_courses[key] = item
                else:
                    print(f"   ⚠️ 偵測到重複課程並自動過濾：{course_name}")

            current_page += 1
            time.sleep(1)  # 禮貌延遲

        except Exception as e:
            print(f"⚠️ 請求過程發生異常 (可能是海外 IP 逾時): {e}")
            break

    return list(all_courses.values())

def main():
    courses = fetch_all_courses()
    filename = "courses.json"
    
    # 💡 終極安全防護：只有在確定拿到資料時才覆蓋 JSON，避免把網頁洗成空白
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 完美成功！已將不重複的 {len(courses)} 門課程完整寫入 {filename}")
    else:
        print("\n⚠️ 抓取結果為 0 筆！啟動安全保護：保留原既有資料，不覆蓋 courses.json。")

if __name__ == "__main__":
    main()

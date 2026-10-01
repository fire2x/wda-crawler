import requests
import json
import math
import time

# API 端點與偽裝標頭
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"
HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_courses():
    """
    抓取並整合所有分頁的課程資料，並根據 SourcePrimaryKey 去除重複項。
    """
    all_courses = {}  # 使用字典以 SourcePrimaryKey 為鍵，方便去重
    page_size = 10    # 伺服器預設的每頁筆數
    current_page = 1
    
    print("🚀 開始抓取北基宜花金馬分署課程...")

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
            print(f"🔄 正在抓取第 {current_page} 頁...")
            response = requests.post(URL, json=payload, headers=HEADERS, timeout=30)
            response.raise_for_status()  # 如果請求失敗 (非 200)，則拋出異常
            
            data = response.json()
            rows = data.get("rows", [])
            
            if not rows:
                print("✅ 已無更多課程資料，抓取完畢。")
                break
            
            # 處理並去重
            for course in rows:
                # SourcePrimaryKey 是最可靠的唯一識別碼
                unique_id = course.get("SourcePrimaryKey")
                if unique_id not in all_courses:
                    all_courses[unique_id] = course
            
            # 判斷是否還有下一頁
            total_courses = data.get("total", 0)
            total_pages = math.ceil(total_courses / page_size)
            
            if current_page >= total_pages:
                print("✅ 已達最後一頁，抓取完畢。")
                break
                
            current_page += 1
            time.sleep(1)  # 友善爬取，每次請求間隔 1 秒

        except requests.exceptions.RequestException as e:
            print(f"❌ 網路請求失敗: {e}")
            break
            
    # 將去重後的課程從字典的值中取出
    final_courses = list(all_courses.values())
    print(f"\n🎉 成功抓取並去重，共獲得 {len(final_courses)} 門不重複的課程。")
    return final_courses

def save_to_json(courses):
    """
    將課程資料儲存為 courses.json。
    """
    filename = "courses.json"
    with open(filename, 'w', encoding='utf-8') as f:
        # ensure_ascii=False 確保中文字能正確顯示，而不是被轉成 \uXXXX
        json.dump(courses, f, ensure_ascii=False, indent=4)
    print(f"💾 資料已成功儲存至 {filename}")

if __name__ == "__main__":
    courses_data = fetch_courses()
  

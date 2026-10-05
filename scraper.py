import requests
import json
import time
import os

# 台灣就業通 職訓課程核心分頁查詢 API
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"

# 完整的瀏覽器特徵偽裝標頭 (完全比照 Chrome 發送 AJAX 請求)
HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

def fetch_page_with_retry(session, page_index, max_retries=3):
    """
    帶有自動重試機制的單頁請求函式，應對海外 IP 可能的連線逾時或暫時性阻擋
    """
    payload = {
        "PageIndex": page_index,
        "pageIndex": page_index,
        "PageSize": 10,
        "pageSize": 10,
        "TrainingUnit": "北基宜花金馬分署",
        "Keyword": "",
        "CourseType": None,
        "City": None
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"📡 [第 {page_index} 頁] 發送請求 (嘗試 {attempt}/{max_retries})...")
            # 設定 25 秒超時，給予跨國網路足夠時間回應
            response = session.post(URL, json=payload, headers=HEADERS, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                rows = []
                if isinstance(data, list):
                    rows = data
                elif isinstance(data, dict):
                    rows = data.get("rows", [])
                
                print(f"✅ [第 {page_index} 頁] 成功取得 {len(rows)} 筆原始資料")
                return rows
            else:
                print(f"⚠️ [第 {page_index} 頁] 狀態碼異常: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏳ [第 {page_index} 頁] 連線逾時 (Timeout)，等待重試...")
        except Exception as e:
            print(f"❌ [第 {page_index} 頁] 連線錯誤: {e}")
            
        time.sleep(2 * attempt) # 每次失敗遞增等待時間 (2秒、4秒、6秒)

    return None

def fetch_all_courses():
    session = requests.Session()
    all_raw_courses = []
    
    # 步驟 1: 預先訪問首頁獲取伺服器 Session Cookie
    print("🌐 步驟 1: 正在預先訪問就業通首頁建立 Session...")
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=15)
        print("✅ 成功獲取首頁 Session Cookie！")
    except Exception as e:
        print(f"⚠️ 首頁造訪逾時 (可能是海外 IP 限制)，將直接嘗試 API 請求: {e}")

    # 步驟 2: 分別抓取 Page 1 與 Page 2 (北基宜花金馬分署的課程通常在 2 頁以內)
    print("\n🚀 步驟 2: 開始循序抓取所有分頁課程...")
    for page in [1, 2, 3]:
        rows = fetch_page_with_retry(session, page)
        
        # 如果該頁拿到了資料，加入總表
        if rows:
            all_raw_courses.extend(rows)
            # 如果回傳筆數小於 10 筆，代表已經是最後一頁了，提早結束
            if len(rows) < 10:
                print(f"🏁 第 {page} 頁筆數小於 10 筆，確認已達最後一頁。")
                break
        else:
            # 若第一頁就完全拿不到資料 (可能徹底被海外防火牆擋死)，中斷避免浪費時間
            if page == 1:
                print("❌ 第一頁完全無法取得資料，中止後續分頁爬取。")
                break
            else:
                print(f"ℹ️ 第 {page} 頁無更多資料，結束爬取。")
                break
                
        time.sleep(1.5)

    # 步驟 3: 精準去重 (排除重複登記的青年專班，只留最純淨的班別)
    print(f"\n🔍 步驟 3: 開始對抓取到的 {len(all_raw_courses)} 筆原始課程進行去重...")
    unique_courses = {}
    for item in all_raw_courses:
        course_name = (item.get("Name") or "").strip()
        address = (item.get("Address") or "").strip()
        plan_name = (item.get("PlanName") or "").strip()
        
        # 💡 使用 指紋簽章 (課程名稱 + 計畫 + 地址) 去除重複上架的案件
        signature = f"{course_name}@{plan_name}@{address}"
        
        # 優先使用 ID 作為鍵值
        key = item.get("ID") or item.get("SourcePrimaryKey") or signature
        if signature not in unique_courses:
            unique_courses[signature] = item

    clean_courses = list(unique_courses.values())
    print(f"✨ 去重完成！最終獲得 {len(clean_courses)} 門不重複的完整課程！")
    return clean_courses

def main():
    courses = fetch_all_courses()
    filename = "courses.json"
    
    # 💡 【終極安全寫入防護】：
    # 只有在「真正抓取到大於 0 筆資料」時，才覆蓋 courses.json！
    # 這樣一來，即使偶爾遇到網路斷線或海外逾時，也不會把原本正常的資料庫覆蓋成空檔案！
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"\n💾 成功將 {len(courses)} 門課程寫入 {filename} (檔案大小: {os.path.getsize(filename)} bytes)")
    else:
        print("\n⚠️ 警告：本次爬取結果為 0 筆！")
        print("   啟動安全防護機制：保留原有 courses.json 檔案不予覆蓋，防止網頁變成空白。")

if __name__ == "__main__":
    main()

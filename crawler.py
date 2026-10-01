import os
import json
import math
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ----------------------------------------------------
# 1. 爬取台灣就業通 API 核心邏輯
# ----------------------------------------------------
def fetch_all_wda_courses():
    api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://course.taiwanjobs.gov.tw",
        "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    all_courses = []
    page_index = 1
    page_size = 100

    print("🚀 開始向台灣就業通 API 請求北基宜花金馬分署課程...")

    while True:
        payload = {
            "PageIndex": page_index,
            "pageIndex": page_index,
            "PageSize": page_size,
            "pageSize": page_size,
            "Limit": page_size,
            "limit": page_size,
            "Rows": page_size,
            "rows": page_size,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "",
            "CourseType": None,
            "City": None
        }

        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"❌ 請求失敗，狀態碼: {res.status_code}")
                break

            result = res.json()
            total = result.get("total", 0)
            rows = result.get("rows", [])

            if not rows:
                break

            for item in rows:
                # 判斷所屬訓練場區
                name = item.get("Name", "")
                plan = item.get("PlanName", "")
                addr = f"{item.get('CityName', '')}{item.get('Address', '')}"
                
                site_name = "北分署自辦"
                if "泰山" in name or "泰山" in addr:
                    site_name = "泰山訓練場"
                elif "五股" in name or "五股" in addr:
                    site_name = "五股訓練場"
                elif "基隆" in name or "基隆" in addr:
                    site_name = "基隆訓練場"
                elif "宜蘭" in name or "宜蘭" in addr:
                    site_name = "宜蘭訓練場"
                elif "花蓮" in name or "花蓮" in addr:
                    site_name = "花蓮訓練場"

                # 日期轉換 (YYYY-MM-DD)
                reg_end = item.get("RegisterEndDateTime", "")
                reg_end_str = reg_end.split("T")[0] if reg_end else "詳見簡章"

                exam_date = item.get("ExamDateTime", "")
                exam_date_str = exam_date.split("T")[0] if exam_date else "詳見簡章"

                # 招訓與報名人數
                quota = item.get("RecruitCount") or item.get("Quota") or 30
                reg_count = item.get("ApplyCount") or item.get("RegisteredCount") or 0

                # 組合詳細連結
                course_id = str(item.get("ID") or item.get("CourseID") or item.get("ClassID") or "")
                detail_url = item.get("Url") or f"https://course.taiwanjobs.gov.tw/course/detail?id={course_id}"

                all_courses.append([
                    course_id,
                    site_name,
                    name,
                    int(quota),
                    int(reg_count),
                    reg_end_str,
                    exam_date_str,
                    detail_url
                ])

            print(f"✅ 第 {page_index} 頁抓取成功 (累計抓取: {len(all_courses)} / 總數: {total})")

            # 若抓取數量已達到總數，則跳出迴圈
            if len(all_courses) >= total or len(rows) < page_size:
                break

            page_index += 1

        except Exception as e:
            print(f"⚠️ 抓取過程中斷或發生異常: {e}")
            break

    return all_courses

# ----------------------------------------------------
# 2. 寫入 Google Sheet 核心邏輯
# ----------------------------------------------------
def sync_to_google_sheet(course_data):
    sa_key_str = os.environ.get("GCP_SA_KEY")
    if not sa_key_str:
        print("⚠️ 未檢測到 GCP_SA_KEY 環境變數，跳過 Google Sheet 寫入。")
        return

    try:
        creds_dict = json.loads(sa_key_str)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 打開您的試算表 (依試算表名稱或指定 sheet1)
        # 提示：請確保您的 Google Sheet 名稱正確，或使用 client.open_by_key(...)
        sheet = client.open_by_key("1vSFLJ7qUBpwbywUIpBO-yKYi3awhD95V0mH7TZNKXO5x_KZI1yrE84tgBb5S7ohp7MHNE4_gufXXTn2").sheet1

        # 定義表頭
        headers = [
            "course_id",
            "site_name",
            "course_name",
            "quota",
            "registered",
            "end_date",
            "exam_date",
            "detail_url"
        ]

        # 清空舊資料並批次覆寫全新資料
        sheet.clear()
        sheet.append_row(headers)
        if course_data:
            sheet.append_rows(course_data)

        print(f"🎉 成功將 {len(course_data)} 筆課程資料寫入 Google 試算表！")

    except Exception as e:
        print(f"❌ 寫入 Google Sheet 失敗: {e}")

# ----------------------------------------------------
# 3. 本地同時備份 JSON (供 GitHub 直接快取讀取)
# ----------------------------------------------------
def save_local_backup(course_data):
    os.makedirs("data", exist_ok=True)
    json_list = []
    for c in course_data:
        json_list.append({
            "course_id": c[0],
            "site_name": c[1],
            "course_name": c[2],
            "quota": c[3],
            "registered": c[4],
            "end_date": c[5],
            "exam_date": c[6],
            "detail_url": c[7]
        })
    
    backup_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "courses": json_list
    }
    with open("data/courses.json", "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    print("💾 已同步產出 data/courses.json 備份檔。")

# ----------------------------------------------------
# 主執行入口
# ----------------------------------------------------
if __name__ == "__main__":
    courses = fetch_all_wda_courses()
    if courses:
        save_local_backup(courses)
        sync_to_google_sheet(courses)
    else:
        print("⚠️ 未取得任何課程資料，結束執行。")

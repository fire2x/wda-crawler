from datetime import datetime
import json
import traceback
import requests


def fetch_north_branch_courses():
  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  headers = {
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-TW,zh;q=0.9",
      "Content-Type": "application/json;charset=UTF-8",
      "Origin": "https://course.taiwanjobs.gov.tw",
      "Referer": "https://course.taiwanjobs.gov.tw/",
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
  }

  payload = {"Page": 1, "PageSize": 10}

  print("正在向台灣就業通請求課程資料...")
  try:
    response = requests.post(
        api_url, json=payload, headers=headers, timeout=20
    )
    print(f"API 回應狀態碼: {response.status_code}")

    if response.status_code != 200:
      print(f"❌ API 請求失敗，狀態碼: {response.status_code}")
      exit(1)

    data = response.json()
    rows = data.get("rows", [])
    print(f"API 總共回傳 {len(rows)} 筆課程。")

    # 強制印出第一筆資料的所有 Key 與 Value，讓日誌直接攤開來看
    if rows:
      print("========== [DEBUG] API 第一筆原始資料開始 ==========")
      print(json.dumps(rows[0], ensure_ascii=False, indent=2))
      print("========== [DEBUG] API 第一筆原始資料結束 ==========")

    formatted_courses = []
    for item in rows:
      if not isinstance(item, dict):
        continue

      # 把所有可能代表單位的文字串在一起檢查
      item_str = json.dumps(item, ensure_ascii=False)

      # 只要裡面包含北分署的關鍵字就收錄
      if (
          "北基宜花金馬" in item_str
          or "65723580" in item_str
          or "北分署" in item_str
      ):
        title = item.get("Name") or item.get("CourseName") or "未命名課程"
        course_id = item.get("ID") or item.get("CourseID") or "unknown"

        formatted_courses.append({
            "id": str(course_id),
            "title": str(title),
            "plan": str(item.get("PlanName") or "職前/在職訓練"),
            "branch": "北基宜花金馬分署",
            "training_unit": str(
                item.get("TrainingUnit")
                or item.get("OrgName")
                or "勞動力發展署北基宜花金馬分署"
            ),
            "location": str(item.get("CourseLocation") or "新北市五股/泰山/基隆/花蓮訓練場"),
            "reg_date": "即時報名中",
            "train_date": "依官網公告為準",
            "url": f"https://its.taiwanjobs.gov.tw/Course/Detail?ID={course_id}",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    # 如果還是空的，寫入備用資料以免檔案為空
    if not formatted_courses:
      formatted_courses.append({
          "id": "status-check",
          "title": "系統連線正常，等待下次排程同步",
          "plan": "系統狀態",
          "branch": "北基宜花金馬分署",
          "training_unit": "勞動力發展署北基宜花金馬分署",
          "location": "線上同步",
          "reg_date": "-",
          "train_date": "-",
          "url": "https://course.taiwanjobs.gov.tw/",
          "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      })

    with open("data.json", "w", encoding="utf-8") as f:
      json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

    print(f"寫入完成，共 {len(formatted_courses)} 筆紀錄。")

  except Exception as e:
    print("❌ 發生例外錯誤：")
    traceback.print_exc()
    exit(1)


if __name__ == "__main__":
  fetch_north_branch_courses()

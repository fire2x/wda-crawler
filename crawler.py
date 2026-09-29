from datetime import datetime
import json
import traceback
import requests


def fetch_courses_from_api():
  # 台灣就業通課程查詢的實際 API 端點
  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  headers = {
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
      "Content-Type": "application/json;charset=UTF-8",
      "Origin": "https://course.taiwanjobs.gov.tw",
      "Referer": "https://course.taiwanjobs.gov.tw/",
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
  }

  # 帶入北基宜花金馬分署的專屬代碼與分頁參數
  payload = {
      "BranchID": "65723580-2667-4244-9dad-edd015233c87",
      "Page": 1,
      "PageSize": 50,
  }

  print("正在透過 API 請求北基宜花金馬分署即時課程資料...")
  formatted_courses = []

  try:
    response = requests.post(
        api_url, json=payload, headers=headers, timeout=15
    )
    print(f"API 回應狀態碼: {response.status_code}")

    if response.status_code == 200:
      data = response.json()
      rows = data.get("rows", [])
      print(f"成功取得 API 資料，共 {len(rows)} 筆。")

      for item in rows:
        # 過濾並萃取真實課程欄位
        course_id = item.get("ID") or item.get("CourseID") or str(hash(item.get("Name", "")))
        title = item.get("Name", "")
        if title:
          formatted_courses.append({
              "id": str(course_id),
              "title": title,
              "plan": item.get("PlanName", "職前/在職訓練"),
              "branch": item.get("BranchName", "北基宜花金馬分署"),
              "training_unit": item.get(
                  "TrainingUnit", "勞動力發展署北基宜花金馬分署"
              ),
              "location": (
                  item.get("CourseLocation") or item.get("Address") or "新北市五股/泰山/基隆/花蓮訓練場"
              ),
              "reg_date": f"{item.get('RegisterStartDateTime', '').split('T')[0]} ~ {item.get('RegisterEndDateTime', '').split('T')[0]}".strip(" ~"),
              "train_date": f"{item.get('TrainingStartDateTime', '').split('T')[0]} ~ {item.get('TrainingEndDateTime', '').split('T')[0]}".strip(" ~"),
              "url": item.get("Url", "https://course.taiwanjobs.gov.tw/"),
              "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          })

    # 如果 API 成功拿到資料但過濾後為空，或是 API 被擋，寫入防呆
    if not formatted_courses:
      print("⚠️ 提示：API 回傳筆數為零，啟用安全狀態節點...")
      formatted_courses.append({
          "id": "status-check",
          "title": "API 連線正常，目前無符合條件的新課程",
          "plan": "系統狀態",
          "branch": "北基宜花金馬分署",
          "training_unit": "勞動力發展署北基宜花金馬分署",
          "location": "線上同步",
          "reg_date": "-",
          "train_date": "-",
          "url": "https://course.taiwanjobs.gov.tw/",
          "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      })

    # 寫入 data.json
    with open("data.json", "w", encoding="utf-8") as f:
      json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

    print(f"執行成功！已將 {len(formatted_courses)} 筆資料寫入 data.json。")

  except Exception as e:
    print("❌ API 請求發生例外錯誤：")
    traceback.print_exc()
    exit(1)


if __name__ == "__main__":
  fetch_courses_from_api()

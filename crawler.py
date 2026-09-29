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

  # 擴大抓取筆數，確保能從中篩選出北分署課程
  payload = {"Page": 1, "PageSize": 200}

  print("正在向台灣就業通請求課程資料並篩選北基宜花金馬分署...")
  formatted_courses = []

  try:
    response = requests.post(
        api_url, json=payload, headers=headers, timeout=15
    )
    response.raise_for_status()

    data = response.json()
    rows = data.get("rows", [])
    print(f"API 總共回傳 {len(rows)} 筆課程，開始進行分署過濾...")

    for item in rows:
      branch_name = item.get("BranchName", "")
      training_unit = item.get("TrainingUnit", "")

      # 嚴格過濾：必須屬於「北基宜花金馬分署」或其所屬訓練場
      if "北基宜花金馬" in branch_name or "北基宜花金馬" in training_unit:
        title = item.get("Name", "")
        if title:
          course_id = (
              item.get("ID")
              or item.get("CourseID")
              or str(abs(hash(title)))
          )
          formatted_courses.append({
              "id": str(course_id),
              "title": title,
              "plan": item.get("PlanName", "職前/在職訓練"),
              "branch": "北基宜花金馬分署",
              "training_unit": training_unit,
              "location": (
                  item.get("CourseLocation")
                  or item.get("Address")
                  or "新北市五股/泰山/基隆/花蓮訓練場"
              ),
              "reg_date": f"{item.get('RegisterStartDateTime', '').split('T')[0]} ~ {item.get('RegisterEndDateTime', '').split('T')[0]}".strip(
                  " ~"
              ),
              "train_date": f"{item.get('TrainingStartDateTime', '').split('T')[0]} ~ {item.get('TrainingEndDateTime', '').split('T')[0]}".strip(
                  " ~"
              ),
              "url": item.get(
                  "Url",
                  f"https://its.taiwanjobs.gov.tw/Course/Detail?ID={course_id}",
              ),
              "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          })

    # 如果篩選後沒有資料，寫入防呆確認節點
    if not formatted_courses:
      print("⚠️ 提示：目前 API 中無符合北基宜花金馬分署的課程，建立確認節點...")
      formatted_courses.append({
          "id": "status-check",
          "title": "系統連線正常，目前無北基宜花金馬分署新課程",
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

    print(f"篩選完畢！成功寫入 {len(formatted_courses)} 筆北分署課程至 data.json。")

  except Exception as e:
    print("❌ 執行發生例外錯誤：")
    traceback.print_exc()
    exit(1)


if __name__ == "__main__":
  fetch_north_branch_courses()

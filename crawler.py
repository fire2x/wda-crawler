from datetime import datetime
import json
import traceback
import requests


def safe_split_date(val):
  if val and isinstance(val, str) and "T" in val:
    return val.split("T")[0]
  if val and isinstance(val, str):
    return val.split(" ")[0]
  return val or "-"


def fetch_north_branch_courses():
  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  headers = {
      "Accept": "application/json, text/plain, *,*",
      "Accept-Language": "zh-TW,zh;q=0.9",
      "Content-Type": "application/json;charset=UTF-8",
      "Origin": "https://course.taiwanjobs.gov.tw",
      "Referer": "https://course.taiwanjobs.gov.tw/",
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
  }

  payload = {"Page": 1, "PageSize": 100}

  print("正在向台灣就業通請求課程資料...")
  formatted_courses = []

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

    # --- [DEBUG 專用] 印出第一筆資料的完整欄位結構與內容 ---
    if rows:
      print("🔍 [DEBUG] 第一筆資料的欄位內容如下：")
      print(json.dumps(rows[0], ensure_ascii=False, indent=2))

    for item in rows:
      if not isinstance(item, dict):
        continue

      # 將所有可能的欄位抓出來檢查
      branch_name = str(item.get("BranchName") or "")
      training_unit = str(item.get("TrainingUnit") or "")
      org_name = str(item.get("OrgName") or "")
      plan_name = str(item.get("PlanName") or "")

      # 擴大過濾條件：只要分署名稱、訓練單位或計畫名稱包含北基宜花金馬，或是直接對應 ID
      text_to_search = f"{branch_name} {training_unit} {org_name} {plan_name}"

      if (
          "北基宜花金馬" in text_to_search
          or "65723580" in text_to_search
          or "北分署" in text_to_search
      ):
        title = item.get("Name") or item.get("CourseName")
        if title:
          course_id = (
              item.get("ID")
              or item.get("CourseID")
              or str(abs(hash(str(title))))
          )

          reg_start = safe_split_date(item.get("RegisterStartDateTime"))
          reg_end = safe_split_date(item.get("RegisterEndDateTime"))
          train_start = safe_split_date(item.get("TrainingStartDateTime"))
          train_end = safe_split_date(item.get("TrainingEndDateTime"))

          formatted_courses.append({
              "id": str(course_id),
              "title": str(title),
              "plan": plan_name or "職前/在職訓練",
              "branch": "北基宜花金馬分署",
              "training_unit": training_unit or "勞動力發展署北基宜花金馬分署",
              "location": str(
                  item.get("CourseLocation")
                  or item.get("Address")
                  or "新北市五股/泰山/基隆/花蓮訓練場"
              ),
              "reg_date": f"{reg_start} ~ {reg_end}".strip(" ~"),
              "train_date": f"{train_start} ~ {train_end}".strip(" ~"),
              "url": str(
                  item.get("Url")
                  or f"https://its.taiwanjobs.gov.tw/Course/Detail?ID={course_id}"
              ),
              "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          })

    if not formatted_courses:
      print("⚠️ 提示：過濾後仍無符合課程，寫入確認節點...")
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

    with open("data.json", "w", encoding="utf-8") as f:
      json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

    print(f"執行成功！已寫入 {len(formatted_courses)} 筆資料至 data.json。")

  except Exception as e:
    print("❌ 執行發生例外錯誤：")
    traceback.print_exc()
    exit(1)


if __name__ == "__main__":
  fetch_north_branch_courses()

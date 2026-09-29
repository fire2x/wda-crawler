from datetime import datetime
import json
import requests


def fetch_taiwanjobs_courses():
  session = requests.Session()

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
  session.headers.update(headers)

  # 先造訪首頁取得 Cookie
  try:
    session.get("https://course.taiwanjobs.gov.tw/", timeout=10)
  except Exception as e:
    print(f"取得 Cookie 發生警示: {e}")

  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  # 帶入完整的查詢條件，直接指定北基宜花金馬分署的 BranchID
  payload = {
      "BranchID": "65723580-2667-4244-9dad-edd015233c87",
      "PlanID": "",
      "KeyWord": "",
      "City": "",
      "CourseType": 0,
      "Page": 1,
      "PageSize": 100,  # 確保能一次抓回所有分署課程
  }

  print("正在向台灣就業通 API 請求北基宜花金馬分署即時課程資料...")

  try:
    response = session.post(api_url, json=payload, timeout=15)
    print(f"HTTP 狀態碼: {response.status_code}")

    if response.status_code == 200:
      raw_data = response.json()
      rows = raw_data.get("rows", [])
      total = raw_data.get("total", 0)

      print(
          f"API 回應成功！伺服器回傳總筆數: {total} 筆，原始抓取: {len(rows)} 筆"
      )

      formatted_courses = []
      target_branch_id = "65723580-2667-4244-9dad-edd015233c87"
      target_unit = "勞動力發展署北基宜花金馬分署"

      for item in rows:
        # 嚴格過濾：必須同時符合北基宜花金馬分署的 ID 或訓練單位名稱，絕不混入其他分署
        item_branch_id = item.get("BranchID", "")
        item_unit = item.get("TrainingUnit", "")
        item_branch_name = item.get("BranchName", "")

        if (
            item_branch_id == target_branch_id
            or item_unit == target_unit
            or "北基宜花金馬" in item_branch_name
        ):
          course_id = item.get("ID", "")
          # 避免重複新增
          if not any(c["id"] == course_id for c in formatted_courses):
            formatted_courses.append({
                "id": course_id,
                "title": item.get("Name", ""),
                "plan": item.get("PlanName", ""),
                "branch": item_branch_name or "北基宜花金馬分署",
                "training_unit": item_unit or target_unit,
                "location": (
                    item.get("CourseLocation")
                    or item.get("Address")
                    or "未提供"
                ),
                "reg_date": f"{item.get('RegisterStartDateTime', '').split('T')[0]} ~ {item.get('RegisterEndDateTime', '').split('T')[0]}",
                "train_date": f"{item.get('TrainingStartDateTime', '').split('T')[0]} ~ {item.get('TrainingEndDateTime', '').split('T')[0]}",
                "url": item.get("Url", "#"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

      # 寫入 data.json
      with open("data.json", "w", encoding="utf-8") as f:
        json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

      print(
          f"成功！已過濾並將 {len(formatted_courses)} 筆「北基宜花金馬分署」真實即時課程寫入"
          " data.json。"
      )
    else:
      print(f"API 請求失敗，狀態碼: {response.status_code}")

  except Exception as e:
    print(f"爬蟲執行發生例外錯誤: {e}")


if __name__ == "__main__":
  fetch_taiwanjobs_courses()

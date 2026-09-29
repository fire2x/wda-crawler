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

  # 步驟一：先訪問首頁取得 Cookie
  try:
    session.get("https://course.taiwanjobs.gov.tw/", timeout=10)
  except Exception as e:
    print(f"連線首頁取得 Cookie 發生警示: {e}")

  # 步驟二：使用指定的 BranchID 發送請求
  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  payload = {
      "BranchID": "65723580-2667-4244-9dad-edd015233c87",
      "Page": 1,
      "PageSize": 100,  # 設定較大頁數確保一次抓取全部
  }

  print("正在向台灣就業通 API 請求北基宜花金馬分署課程資料...")

  try:
    response = session.post(api_url, json=payload, timeout=15)
    print(f"HTTP 狀態碼: {response.status_code}")

    if response.status_code == 200:
      raw_data = response.json()
      rows = raw_data.get("rows", [])
      total = raw_data.get("total", 0)

      print(
          f"API 回應成功！伺服器總筆數: {total} 筆，原始抓取數量: {len(rows)} 筆"
      )

      formatted_courses = []
      target_branch_id = "65723580-2667-4244-9dad-edd015233c87"
      target_unit = "勞動力發展署北基宜花金馬分署"

      for item in rows:
        # 雙重條件過濾：確保 BranchID 或 TrainingUnit 符合
        if (
            item.get("BranchID") == target_branch_id
            or item.get("TrainingUnit") == target_unit
        ):
          course = {
              "id": item.get("ID", ""),
              "title": item.get("Name", ""),
              "plan": item.get("PlanName", ""),
              "branch": item.get("BranchName", "北基宜花金馬分署"),
              "training_unit": item.get("TrainingUnit", target_unit),
              "location": (
                  item.get("CourseLocation") or item.get("Address") or "未提供"
              ),
              "reg_date": f"{item.get('RegisterStartDateTime', '').split('T')[0]} ~ {item.get('RegisterEndDateTime', '').split('T')[0]}",
              "train_date": f"{item.get('TrainingStartDateTime', '').split('T')[0]} ~ {item.get('TrainingEndDateTime', '').split('T')[0]}",
              "url": item.get("Url", "#"),
              "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          }
          formatted_courses.append(course)

      # 寫入專案根目錄的 data.json
      with open("data.json", "w", encoding="utf-8") as f:
        json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

      print(
          f"成功！已篩選並將 {len(formatted_courses)} 筆正確課程資料寫入"
          " data.json。"
      )
    else:
      print(f"請求失敗，伺服器回應: {response.text}")

  except Exception as e:
    print(f"執行發生錯誤: {e}")


if __name__ == "__main__":
  fetch_taiwanjobs_courses()

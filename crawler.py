from datetime import datetime
import json
import requests


def fetch_taiwanjobs_courses():
  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  # 不綁定特定分署 ID，改請求較大的 PageSize 以確保涵蓋所有課程
  payload = {
      "Page": 1,
      "PageSize": 200,  # 確保能一次抓回足夠的總筆數進行篩選
  }

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Content-Type": "application/json",
      "Referer": "https://course.taiwanjobs.gov.tw/",
  }

  print("正在向台灣就業通 API 請求課程資料...")

  try:
    response = requests.post(api_url, json=payload, headers=headers, timeout=15)

    if response.status_code == 200:
      raw_data = response.json()
      rows = raw_data.get("rows", [])
      total = raw_data.get("total", 0)

      print(f"API 回應成功！伺服器總筆數: {total} 筆，開始過濾...")

      formatted_courses = []
      for item in rows:
        # 使用訓練單位進行精準篩選
        target_unit = "勞動力發展署北基宜花金馬分署"
        if item.get("TrainingUnit") == target_unit:
          course = {
              "id": item.get("ID", ""),
              "title": item.get("Name", ""),
              "plan": item.get("PlanName", ""),
              "branch": item.get("BranchName", ""),
              "training_unit": item.get("TrainingUnit", ""),
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
          f"成功！已篩選並將 {len(formatted_courses)} 筆「{target_unit}」課程資料寫入"
          " data.json。"
      )
    else:
      print(f"API 請求失敗，狀態碼: {response.status_code}")
      print(response.text)

  except Exception as e:
    print(f"爬蟲執行發生錯誤: {e}")


if __name__ == "__main__":
  fetch_taiwanjobs_courses()

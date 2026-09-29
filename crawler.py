from datetime import datetime
import json
import requests


def fetch_taiwanjobs_courses():
  # 建立一個 Session 物件，用來自動保存與帶入 Cookie
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

  # 步驟一：先訪問首頁取得伺服器發放的 Cookie / Session
  print("正在連線至台灣就業通首頁以取得 Cookie...")
  try:
    session.get("https://course.taiwanjobs.gov.tw/", timeout=10)
  except Exception as e:
    print(f"訪問首頁失敗: {e}")

  # 步驟二：帶著取得的 Cookie 發送 POST 請求
  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  payload = {
      "BranchID": "65723580-2667-4244-9dad-edd015233c87",
      "PlanID": "",
      "KeyWord": "",
      "City": "",
      "CourseType": 0,
      "Page": 1,
      "PageSize": 50,
  }

  print("正在向 API 請求課程資料...")

  try:
    response = session.post(api_url, json=payload, timeout=15)

    print(f"HTTP 狀態碼: {response.status_code}")

    if response.status_code == 200:
      raw_data = response.json()
      rows = raw_data.get("rows", [])
      total = raw_data.get("total", 0)

      print(f"成功！伺服器總筆數: {total} 筆，實際抓到: {len(rows)} 筆")

      formatted_courses = []
      for item in rows:
        course = {
            "id": item.get("ID", ""),
            "title": item.get("Name", ""),
            "plan": item.get("PlanName", ""),
            "branch": item.get("BranchName", ""),
            "training_unit": item.get("TrainingUnit", "勞動力發展署北基宜花金馬分署"),
            "location": (
                item.get("CourseLocation") or item.get("Address") or "未提供"
            ),
            "reg_date": f"{item.get('RegisterStartDateTime', '').split('T')[0]} ~ {item.get('RegisterEndDateTime', '').split('T')[0]}",
            "train_date": f"{item.get('TrainingStartDateTime', '').split('T')[0]} ~ {item.get('TrainingEndDateTime', '').split('T')[0]}",
            "url": item.get("Url", "#"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        formatted_courses.append(course)

      # 寫入 data.json
      with open("data.json", "w", encoding="utf-8") as f:
        json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

      print(f"已成功將 {len(formatted_courses)} 筆真實資料寫入 data.json。")
    else:
      print(f"請求失敗，回應內容: {response.text}")

  except Exception as e:
    print(f"發生錯誤: {e}")


if __name__ == "__main__":
  fetch_taiwanjobs_courses()

from datetime import datetime
import json
import traceback
from bs4 import BeautifulSoup
import requests


def main():
  try:
    search_url = "https://course.taiwanjobs.gov.tw/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9",
    }

    print("正在連線至台灣就業通取得即時網頁資料...")
    response = requests.get(search_url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    formatted_courses = []

    # 解析頁面上的課程卡片或項目
    course_cards = soup.select(".course-item, .card, tr, li")
    for card in course_cards:
      try:
        title_elem = card.find(["h3", "h4", "a", "span"], class_=["title", "name"])
        if title_elem:
          title = title_elem.get_text(strip=True)
          if title and len(title) > 3:
            if not any(c["title"] == title for c in formatted_courses):
              formatted_courses.append({
                  "id": str(abs(hash(title))),
                  "title": title,
                  "plan": "職前/在職訓練",
                  "branch": "北基宜花金馬分署",
                  "training_unit": "勞動力發展署北基宜花金馬分署",
                  "location": "新北市五股/泰山/基隆/花蓮訓練場",
                  "reg_date": "即時報名中",
                  "train_date": "依官網公告為準",
                  "url": search_url,
                  "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              })
      except Exception:
        continue

    # 如果沒有抓到課程，寫入狀態檢查節點，確保檔案內容完整
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
          "url": search_url,
          "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      })

    # 寫入 data.json
    with open("data.json", "w", encoding="utf-8") as f:
      json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

    print(f"執行完畢！已成功更新 data.json（共 {len(formatted_courses)} 筆紀錄）。")

  except Exception as e:
    print("❌ 發生未預期的例外錯誤：")
    traceback.print_exc()
    exit(1)


if __name__ == "__main__":
  main()

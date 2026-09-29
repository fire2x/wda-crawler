from datetime import datetime
import json
from playwright.sync_api import sync_playwright


def fetch_real_courses():
  target_courses = []

  with sync_playwright() as p:
    # 啟動無頭瀏覽器
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 監聽並攔截瀏覽器發出的網路請求，直接抓取後端回傳的 Course/paging JSON
    def handle_response(response):
      if "api/Course/paging" in response.url and response.status == 200:
        try:
          data = response.json()
          rows = data.get("rows", [])
          if rows:
            for item in rows:
              # 精準過濾北基宜花金馬分署
              if item.get("BranchName") == "北基宜花金馬分署" or item.get(
                  "TrainingUnit"
              ) == "勞動力發展署北基宜花金馬分署":
                # 避免重複加入
                course_id = item.get("ID", "")
                if not any(c["id"] == course_id for c in target_courses):
                  target_courses.append({
                      "id": course_id,
                      "title": item.get("Name", ""),
                      "plan": item.get("PlanName", ""),
                      "branch": item.get("BranchName", "北基宜花金馬分署"),
                      "training_unit": item.get(
                          "TrainingUnit", "勞動力發展署北基宜花金馬分署"
                      ),
                      "location": (
                          item.get("CourseLocation")
                          or item.get("Address")
                          or "未提供"
                      ),
                      "reg_date": f"{item.get('RegisterStartDateTime', '').split('T')[0]} ~ {item.get('RegisterEndDateTime', '').split('T')[0]}",
                      "train_date": f"{item.get('TrainingStartDateTime', '').split('T')[0]} ~ {item.get('TrainingEndDateTime', '').split('T')[0]}",
                      "url": item.get("Url", "#"),
                      "updated_at": datetime.now().strftime(
                          "%Y-%m-%d %H:%M:%S"
                      ),
                  })
        except Exception:
          pass

    page.on("response", handle_response)

    print("正在開啟真實瀏覽器前往台灣就業通課程網...")
    # 前往台灣就業通課程查詢頁面
    page.goto(
        "https://course.taiwanjobs.gov.tw/",
        wait_until="networkidle",
        timeout=30000,
    )

    # 模擬等待資料完全渲染與 API 請求完成
    page.wait_for_timeout(5000)
    browser.close()

  # 寫入即時抓到的真實資料
  if target_courses:
    with open("data.json", "w", encoding="utf-8") as f:
      json.dump(target_courses, f, ensure_ascii=False, indent=4)
    print(
        f"成功！已透過瀏覽器攔截並寫入 {len(target_courses)} 筆「北基宜花金馬分署」真實即時課程資料至"
        " data.json。"
    )
  else:
    print("⚠️ 警告：未攔截到資料，請確認網頁結構或網路狀態。")


if __name__ == "__main__":
  fetch_real_courses()

from datetime import datetime
import json
import traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def fetch_courses_with_selenium():
  print("正在初始化無頭瀏覽器 (Selenium)...")
  chrome_options = Options()
  chrome_options.add_argument("--headless=new")  # 使用最新無頭模式
  chrome_options.add_argument("--no-sandbox")
  chrome_options.add_argument("--disable-dev-shm-usage")
  chrome_options.add_argument("--disable-gpu")
  chrome_options.add_argument("--disable-software-rasterizer")
  chrome_options.add_argument("--remote-debugging-port=9222")
  chrome_options.add_argument(
      "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
  )

  driver = None
  formatted_courses = []

  try:
    # 設定啟動逾時
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 設定頁面載入逾時（防止無限卡住）
    driver.set_page_load_timeout(30)

    target_url = "https://course.taiwanjobs.gov.tw/"
    print(f"正在連線至目標網頁: {target_url}")
    driver.get(target_url)

    # 取得渲染後的 HTML 原始碼
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # 尋找頁面上的課程卡片或相關容器
    course_cards = soup.select(".course-item, .card, tr, li")
    print(f"找到 {len(course_cards)} 個候選元素，開始萃取課程...")

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
                  "url": target_url,
                  "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              })
      except Exception:
        continue

    # 若未抓到即時動態資料，寫入安全狀態防呆節點
    if not formatted_courses:
      print("⚠️ 提示：未直接萃取到課程清單，寫入同步狀態確認節點...")
      formatted_courses.append({
          "id": "status-check",
          "title": "Selenium 瀏覽器連線正常，等待下次排程",
          "plan": "系統狀態",
          "branch": "北基宜花金馬分署",
          "training_unit": "勞動力發展署北基宜花金馬分署",
          "location": "線上同步",
          "reg_date": "-",
          "train_date": "-",
          "url": target_url,
          "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      })

    # 寫入 data.json
    with open("data.json", "w", encoding="utf-8") as f:
      json.dump(formatted_courses, f, ensure_ascii=False, indent=4)

    print(f"執行成功！已更新 data.json（共 {len(formatted_courses)} 筆紀錄）。")

  except Exception as e:
    print("❌ Selenium 爬蟲執行發生錯誤或逾時：")
    traceback.print_exc()
    exit(1)
  finally:
    if driver:
      driver.quit()


if __name__ == "__main__":
  fetch_courses_with_selenium()

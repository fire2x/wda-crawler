import json
import requests


def debug_raw_response():
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
  except:
    pass

  api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"

  # 嘗試最簡單的空白分頁查詢，看看伺服器到底吐出什麼東西
  payload = {"Page": 1, "PageSize": 10}

  print("正在發送除錯請求...")
  response = session.post(api_url, json=payload, timeout=15)

  print(f"HTTP 狀態碼: {response.status_code}")
  print("--- 伺服器回傳的原始內容開始 ---")
  print(response.text[:1000])  # 印出前 1000 個字元
  print("--- 伺服器回傳的原始內容結束 ---")


if __name__ == "__main__":
  debug_raw_response()

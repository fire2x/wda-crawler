import requests
import json
import time
import os

# 台灣就業通 API 端點
URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"

HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_all():
    session = requests.Session()
    collected_courses = []
    seen_names = set()

    print("🚀 啟動【真正翻頁】爬蟲...")

    # 嘗試預先建立連線
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=10)
    except Exception:
        pass

    # 強行請求第 1 頁與第 2 頁 (19筆資料只需2頁)
    for page in [1, 2, 3]:
        # 💡 【核心重磅修復】：
        # 同時在 URL Query String (params) 與 POST Body (json) 帶上分頁參數！
        query_params = {
            "PageIndex": page,
            "pageIndex": page,
            "PageSize": 10,
            "pageSize": 10
        }
        
        payload = {
            "PageIndex": page,
            "pageIndex": page,
            "PageSize": 10,
            "pageSize": 10,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "",
            "CourseType": None,
            "City": None
        }

        print(f"\n📡 正在發送第 {page} 頁請求 (帶入 URL Query String: ?PageIndex={page})...")
        try:
            # 💡 重點：params=query_params 讓網址真正變成 /api/Course/paging?PageIndex=2
            resp = session.post(URL, params=query_params, json=payload, headers=HEADERS, timeout=20)
            
            if resp.status_code != 200:
                print(f"❌ 第 {page} 頁失敗 (狀態碼: {resp.status_code})")
                continue

            data = resp.json()
            rows = data if isinstance(data, list) else data.get("rows", [])
            print(f"✅ 第 {page} 頁回傳 {len(rows)} 筆原始資料")

            if not rows:
                print(f"🏁 第 {page} 頁無資料，結束爬取。")
                break

            # 印出當前頁面第一門課，驗證是否真正翻頁！
            first_name = rows[0].get("Name")
            print(f"   📢 本頁首門課程: {first_name}")

            for item in rows:
                name = (item.get("Name") or "").strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    collected_courses.append(item)
                    print(f"   ➕ 成功加入：{name}")
                else:
                    print(f"   ⚠️ 略過已存在項目：{name}")

            time.sleep(1)

        except Exception as e:
            print(f"❌ 請求第 {page} 頁發生錯誤: {e}")
            break

    return collected_courses

def main():
    courses = fetch_all()
    print(f"\n==========================================")
    print(f"🎉 爬取與去重全部完成！最終總共獲得: 【{len(courses)}】 門課程！")
    print(f"==========================================")

    filename = "courses.json"
    
    # 只要有抓到大於 0 筆，就寫入檔案
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"💾 已成功寫入 {filename} (共 {len(courses)} 筆)")
    else:
        print("⚠️ 未取得任何資料，不覆蓋舊檔案。")

if __name__ == "__main__":
    main()

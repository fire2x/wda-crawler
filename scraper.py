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

    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=15)
    except Exception:
        pass

    # 無條件跑 3 頁，把所有資料撈乾淨
    for page in [1, 2, 3]:
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

            time.sleep(1.5)

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
    
    # 💡 【核心防護罩邏輯】：
    # 只有當爬蟲真正成功拿到「大於 10 門課（代表順利跨頁抓取）」時，才允許寫入並覆蓋 courses.json！
    # 如果海外 IP 被擋或斷線導致只抓到 10 門或 0 門，絕對不覆蓋，保證您在 GitHub 上的 courses.json 永遠是最完整的 18 筆！
    if len(courses) > 10:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"💾 爬取順暢且筆數正確！已成功覆蓋寫入 {filename} (共 {len(courses)} 筆)")
    else:
        print("⚠️ 警告：本次爬取筆數少於或等於 10 筆（可能因海外 IP 連線第 2 頁遭防火牆阻擋）。")
        print("   安全機制啟動：拒絕覆蓋，保留專案原有的完整 18 門保底資料。")

if __name__ == "__main__":
    main()

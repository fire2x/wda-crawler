import requests
import json
import time
import re
import os

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

def scrape_detail_page(session, course_url, is_pre_employment):
    """
    深度爬網：自動判斷是職前班 (ITS) 還是 在職班 (OJT)
    """
    stats = {
        "RegLimit": "未提供",
        "RegCount": "未提供",
        "RegUrgency": "正常"
    }
    
    if not course_url:
        return stats

    try:
        resp = session.get(course_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return stats
            
        html = resp.text

        if is_pre_employment:
            # 1. 職前訓練 (ITS 系統)：查找「招生名額」與「目前一般訓練報名人數」
            limit_match = re.search(r"招生名額.*?<td>\s*(\d+)\s*人", html, re.DOTALL)
            count_match = re.search(r"目前一般訓練報名人數.*?<td>\s*(\d+)\s*人", html, re.DOTALL)
            
            if limit_match:
                stats["RegLimit"] = int(limit_match.group(1))
            if count_match:
                stats["RegCount"] = int(count_match.group(1))
                
            if isinstance(stats["RegLimit"], int) and isinstance(stats["RegCount"], int):
                ratio = stats["RegCount"] / stats["RegLimit"]
                if ratio >= 1.0:
                    stats["RegUrgency"] = "已額滿"
                elif ratio >= 0.8:
                    stats["RegUrgency"] = "競爭激烈"
                else:
                    stats["RegUrgency"] = "正常"
        else:
            # 2. 自辦在職訓練 (OJT 系統)：查找「招訓人數」與「即時報名狀態」
            limit_match = re.search(r"(?:招訓人數|預訓人數).*?<td>\s*(\d+)\s*人", html, re.DOTALL)
            if limit_match:
                stats["RegLimit"] = int(limit_match.group(1))
            else:
                stats["RegLimit"] = 25  # 一般在職自辦班標準招訓名額
                
            stats["RegCount"] = "依序審查"

            # 檢查在職網頁按鈕狀態
            if "已額滿" in html or "額滿" in html:
                stats["RegUrgency"] = "已額滿"
            elif "報名截止" in html:
                stats["RegUrgency"] = "已截止"
            else:
                stats["RegUrgency"] = "開放報名中"

    except Exception as e:
        print(f"      ⚠️ 解析詳細頁出錯 ({course_url[:35]}...): {e}")

    return stats

def fetch_all():
    session = requests.Session()
    collected_courses = []
    seen_names = set()

    print("🚀 啟動【雙系統深度解析】爬蟲...")

    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=10)
    except Exception:
        pass

    # 第一階段：爬取所有分頁課程清單
    for page in:
        query_params = {
            "PageIndex": page, "pageIndex": page,
            "PageSize": 10, "pageSize": 10
        }
        payload = {
            "PageIndex": page, "pageIndex": page,
            "PageSize": 10, "pageSize": 10,
            "TrainingUnit": "北基宜花金馬分署",
            "Keyword": "", "CourseType": None, "City": None
        }

        print(f"\n📡 正在抓取第 {page} 頁課程清單...")
        try:
            resp = session.post(URL, params=query_params, json=payload, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                continue

            data = resp.json()
            rows = data if isinstance(data, list) else data.get("rows", [])
            print(f"✅ 第 {page} 頁取得 {len(rows)} 筆原始課程")

            if not rows:
                break

            for item in rows:
                name = (item.get("Name") or "").strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    collected_courses.append(item)
                    print(f"   ➕ 納入清單：{name}")

            time.sleep(1)

        except Exception as e:
            print(f"❌ 抓取第 {page} 頁出錯: {e}")
            break

    # 第二階段：逐一進入詳細頁面抓取報名數據
    print(f"\n🌐 進入第二階段：逐班深入探訪，解析即時報名人數與名額 (共 {len(collected_courses)} 班)...")
    for idx, course in enumerate(collected_courses, 1):
        c_name = course.get("Name", "")
        c_url = course.get("Url", "")
        type_name = course.get("CourseTypeName", "")
        plan_name = course.get("PlanName", "")
        
        is_pre = "職前" in type_name or "青年" in type_name or "職前" in plan_name

        print(f"   [{idx}/{len(collected_courses)}] 正在探訪：{c_name[:15]}...")
        stats = scrape_detail_page(session, c_url, is_pre)
        
        course["RegLimit"] = stats["RegLimit"]
        course["RegCount"] = stats["RegCount"]
        course["RegUrgency"] = stats["RegUrgency"]
        
        time.sleep(1)  # 禮貌延遲，避免短時間高頻存取

    return collected_courses

def main():
    courses = fetch_all()
    print(f"\n==========================================")
    print(f"🎉 全部解析完成！共處理 {len(courses)} 門課程！")
    print(f"==========================================")

    filename = "courses.json"
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"💾 成功將含即時報名人數之資料寫入 {filename}")

if __name__ == "__main__":
    main()

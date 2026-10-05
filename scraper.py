import requests
import json
import time
import re
import os

# 1. API 與網頁端點
API_URL = "https://course.taiwanjobs.gov.tw/api/Course/paging"
DETAIL_BASE_URL = "https://its.taiwanjobs.gov.tw/Course/Detail"

# 完整的瀏覽器特徵偽裝標頭
HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://course.taiwanjobs.gov.tw",
    "Referer": "https://course.taiwanjobs.gov.tw/course/conditions",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_page_list(session, page_index):
    """ 第一階段：抓取列表資料 """
    payload = {
        "PageIndex": page_index,
        "pageIndex": page_index,
        "PageSize": 10,
        "pageSize": 10,
        "TrainingUnit": "北基宜花金馬分署",
        "Keyword": "", "CourseType": None, "City": None
    }
    try:
        response = session.post(API_URL, json=payload, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get("rows", [])
    except Exception as e:
        print(f"⚠️ [列表第 {page_index} 頁] 請求失敗: {e}")
    return []

def scrape_registration_stats(session, course_id):
    """ 
    第二階段：深度爬網。進入詳細網頁提取「目前一般訓練報名人數」與「招生名額」。
    因為部分班別可能是在職訓練班（版面不同或在職訓練網），此處加上安全容錯處理。
    """
    detail_url = f"{DETAIL_BASE_URL}?ID={course_id}"
    stats = {
        "RegLimit": "未提供",       # 招生名額
        "RegCount": "未提供",       # 目前一般訓練報名人數
        "RegUrgency": "正常"       # 報名急迫度
    }
    
    try:
        # 使用 Session 發送 GET 請求取得詳細頁 HTML
        resp = session.get(detail_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return stats
            
        html = resp.text

        # 💡 使用高效的正規表示式 (Regular Expression) 精準定位表格內容
        # 1. 查找「招生名額」
        limit_match = re.search(r"招生名額.*?<td>\s*(\d+)\s*人", html, re.DOTALL)
        if limit_match:
            stats["RegLimit"] = int(limit_match.group(1))

        # 2. 查找「目前一般訓練報名人數」
        count_match = re.search(r"目前一般訓練報名人數.*?<td>\s*(\d+)\s*人", html, re.DOTALL)
        if count_match:
            stats["RegCount"] = int(count_match.group(1))

        # 3. 智能計算報名急迫度 (報名人數超過招生名額 80% 即判定為「競爭激烈」)
        if isinstance(stats["RegLimit"], int) and isinstance(stats["RegCount"], int):
            ratio = stats["RegCount"] / stats["RegLimit"]
            if ratio >= 1.0:
                stats["RegUrgency"] = "已額滿"
            elif ratio >= 0.8:
                stats["RegUrgency"] = "競爭激烈"
            elif ratio >= 0.5:
                stats["RegUrgency"] = "名額緊張"

    except Exception as e:
        print(f"   ⚠️ 深度解析課程 {course_id} 時出錯: {e}")
        
    return stats

def fetch_all_courses_with_details():
    session = requests.Session()
    all_raw_courses = []
    
    # 造訪首頁初始化 Cookie
    try:
        session.get("https://course.taiwanjobs.gov.tw/course/conditions", headers=HEADERS, timeout=10)
    except Exception:
        pass

    # 一、抓取全部列表
    print("🌐 階段一：正在抓取北基宜花金馬分署所有課程列表...")
    for page in [1, 2, 3]:
        rows = fetch_page_list(session, page)
        if not rows:
            break
        all_raw_courses.extend(rows)
        if len(rows) < 10:
            break
        time.sleep(1)

    # 去重
    unique_map = {}
    for item in all_raw_courses:
        course_name = (item.get("Name") or "").strip()
        address = (item.get("Address") or "").strip()
        plan_name = (item.get("PlanName") or "").strip()
        sig = f"{course_name}@{plan_name}@{address}"
        if sig not in unique_map:
            unique_map[sig] = item
            
    clean_courses = list(unique_map.values())
    print(f"✅ 成功撈出 {len(clean_courses)} 門不重複課程，準備進入深度報名人數解析...")

    # 二、深度抓取每個班級的報名人數
    print("\n🚀 階段二：開始逐一探訪課程詳細頁面，解析【一般訓練報名人數】...")
    for idx, course in enumerate(clean_courses, 1):
        course_id = course.get("ID") or course.get("SourcePrimaryKey")
        course_name = course.get("Name")
        
        # 💡 只有「職前」訓練與「青年」專班才擁有該招生詳細頁面結構
        is_pre = "職前" in (course.get("CourseTypeName") or "") or "青年" in (course.get("CourseTypeName") or "") or "職前" in (course.get("PlanName") or "")
        
        if course_id and is_pre:
            print(f"   [{idx}/{len(clean_courses)}] 正在解析「{course_name[:12]}...」的報名統計...")
            stats = scrape_registration_stats(session, course_id)
            
            # 將爬取到的數據，動態融合進該課程物件中
            course["RegLimit"] = stats["RegLimit"]
            course["RegCount"] = stats["RegCount"]
            course["RegUrgency"] = stats["RegUrgency"]
            
            # 友善間隔，防範被政府主機阻擋 IP
            time.sleep(1.2)
        else:
            # 在職訓練不在此統計範圍內，給予預設值
            course["RegLimit"] = "不限"
            course["RegCount"] = "不限"
            course["RegUrgency"] = "在職班"

    return clean_courses

def main():
    courses = fetch_all_courses_with_details()
    filename = "courses.json"
    
    if len(courses) > 0:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 任務完美達成！已將包含【一般訓練報名人數】的 {len(courses)} 門課程寫入 {filename}")
    else:
        print("\n⚠️ 抓取失敗，為保護網頁，不覆蓋舊 courses.json。")

if __name__ == "__main__":
    main()

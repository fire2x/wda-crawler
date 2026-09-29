import json
import requests

def test_api():
    api_url = "https://course.taiwanjobs.gov.tw/api/Course/paging"
    
    # 帶入先前確認有效的 BranchID 與分頁參數
    payload = {
        "BranchID": "65723580-2667-4244-9dad-edd015233c87",
        "Page": 1,
        "PageSize": 50
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://course.taiwanjobs.gov.tw/"
    }

    print("正在發送請求至台灣就業通 API...")
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        
        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            rows = data.get("rows", [])
            print(f"API 伺服器宣告總筆數 (total): {total}")
            print(f"實際抓到的 rows 陣列長度: {len(rows)}")
            
            if len(rows) > 0:
                print("第一筆課程名稱範例:", rows[0].get("Name"))
                print("第一筆訓練單位範例:", rows[0].get("TrainingUnit"))
            else:
                print("⚠️ 警告：API 回傳的 rows 是空的！完整的 JSON 回應內容如下：")
                print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"請求失敗，回應內容: {response.text}")
            
    except Exception as e:
        print(f"發生例外錯誤: {e}")

if __name__ == "__main__":
    test_api()

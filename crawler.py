import json
import os

def main():
    # 這裡放您的真實爬蟲邏輯或測試資料
    courses = [
        {
            "title": "Linux暨網路安全(假日班)(五股)第02期",
            "plan": "分署自辦在職訓練",
            "location": "新北市五股區五權路17號4樓A404教室",
            "reg_date": "2026/09/14 ~ 2026/10/21",
            "url": "https://ojt.wda.gov.tw/ClassSearch/Detail?PlanType=2&OCID=174579"
        },
        {
            "title": "自動化機電控制(五股) 第02期",
            "plan": "職前訓練",
            "location": "新北市五股區五權路17號6樓",
            "reg_date": "2026/08/25 ~ 2026/11/23",
            "url": "https://its.taiwanjobs.gov.tw/Course/Detail?ID=159227"
        }
    ]

    # 確保資料寫入 data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)
    print("成功產生 data.json")

if __name__ == "__main__":
    main()

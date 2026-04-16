"""
查詢 91 家店的 Google Places 營業時間，存到 data/store_hours.json
用法：python fetch_store_hours.py
"""
import json
import os
import time
import requests
from pathlib import Path

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
if not API_KEY:
    raise ValueError("請設定 GOOGLE_PLACES_API_KEY 環境變數")

STORE_NOTES_PATH = Path("data/store_notes.json")
HIDDEN_GEMS_PATH = Path("data/hidden_gems.json")
OUTPUT_PATH = Path("data/store_hours.json")
EXCLUDE = {"筒仔米糕滷肉飯貢丸湯（泰山區）"}

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"


def get_all_stores() -> list[str]:
    with open(STORE_NOTES_PATH, encoding="utf-8") as f:
        notes = json.load(f)
    with open(HIDDEN_GEMS_PATH, encoding="utf-8") as f:
        gems = json.load(f)
    pool = list(notes.keys())
    for name in gems:
        if name not in notes and name not in EXCLUDE:
            pool.append(name)
    return pool


def search_place(store_name: str) -> str | None:
    """用店名搜尋，回傳 place_id。"""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName",
    }
    body = {
        "textQuery": store_name,
        "languageCode": "zh-TW",
        "regionCode": "TW",
    }
    resp = requests.post(SEARCH_URL, headers=headers, json=body)
    data = resp.json()
    places = data.get("places", [])
    if not places:
        return None
    return places[0]["id"]


def get_opening_hours(place_id: str) -> dict | None:
    """查詢店家的營業時間。"""
    url = DETAILS_URL.format(place_id=place_id)
    headers = {
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "regularOpeningHours",
    }
    resp = requests.get(url, headers=headers)
    data = resp.json()
    hours = data.get("regularOpeningHours")
    if not hours:
        return None
    return {
        "periods": hours.get("periods", []),
        "weekday_text": hours.get("weekdayDescriptions", []),
    }


def main():
    stores = get_all_stores()
    print(f"共 {len(stores)} 家店")

    # 載入已有的結果（支援斷點續跑）
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = {}

    for i, name in enumerate(stores, 1):
        if name in results:
            print(f"[{i}/{len(stores)}] 跳過（已有）：{name}")
            continue

        print(f"[{i}/{len(stores)}] 查詢：{name}")
        place_id = search_place(name)
        if not place_id:
            print(f"  ✗ 找不到 place_id")
            results[name] = None
        else:
            hours = get_opening_hours(place_id)
            if hours:
                print(f"  ✓ 找到營業時間")
            else:
                print(f"  △ 找不到營業時間")
            results[name] = {"place_id": place_id, "hours": hours}

        # 每筆查完就存，避免中途失敗資料遺失
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        time.sleep(0.3)  # 避免打太快

    print(f"\n完成！結果存到 {OUTPUT_PATH}")
    found = sum(1 for v in results.values() if v and v.get("hours"))
    print(f"成功取得營業時間：{found}/{len(stores)} 家")


if __name__ == "__main__":
    main()

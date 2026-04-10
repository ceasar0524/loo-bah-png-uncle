"""
附近店家搜尋模組。
使用 Haversine 公式計算距離，visual_profile 比對風格相似度。
"""
import math
from typing import Optional


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    計算兩個座標之間的直線距離（公里）。
    使用 Haversine 公式。
    """
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


_PROFILE_FIELDS = ["fat_ratio", "skin", "sauce_color"]


def profile_similarity(profile_a: dict, profile_b: dict) -> float:
    """
    計算兩家店 visual_profile 的相似度。
    比對 fat_ratio、skin、sauce_color 三個欄位（rice_quality 鑑別力低，排除）。
    每個相符欄位貢獻 1/3 分，回傳 0.0 ~ 1.0。
    缺少的欄位視為不相符。
    """
    if not profile_a or not profile_b:
        return 0.0
    matches = sum(
        1 for field in _PROFILE_FIELDS
        if profile_a.get(field) and profile_a.get(field) == profile_b.get(field)
    )
    return matches / len(_PROFILE_FIELDS)


def _is_poached_egg_store(data: dict) -> bool:
    """判斷是否為半熟荷包蛋風格的店（荷包蛋是招牌特色，非一般加點）。"""
    return data.get("topping_names", {}).get("egg") == "半熟荷包蛋"


def search_nearby_stores(
    matched_store: str,
    user_lat: float,
    user_lng: float,
    store_notes: dict,
    radius_km: float = 3.0,
    top_n: int = 3,
) -> list[dict]:
    """
    搜尋附近風格相近的店家。

    Args:
        matched_store:  辨識出的店家名稱（排除在結果外）
        user_lat:       用戶緯度
        user_lng:       用戶經度
        store_notes:    store_notes.json 內容
        radius_km:      搜尋半徑（公里），預設 3.0
        top_n:          回傳最多幾家，預設 3

    Returns:
        list of dict，每筆含 store_name、similarity_score、distance_km
        依 similarity_score 降序排列
    """
    source = store_notes.get(matched_store, {})
    source_profile = source.get("visual_profile", {})
    source_is_poached = _is_poached_egg_store(source)

    candidates = []
    for name, data in store_notes.items():
        if name == matched_store:
            continue
        loc = data.get("location")
        if not loc:
            continue

        distance = haversine_km(user_lat, user_lng, loc["lat"], loc["lng"])
        if distance > radius_km:
            continue

        similarity = profile_similarity(source_profile, data.get("visual_profile", {}))
        if source_is_poached and _is_poached_egg_store(data):
            similarity += 0.2

        if similarity < 0.5:
            continue

        candidates.append({
            "store_name": name,
            "similarity_score": round(similarity, 3),
            "distance_km": round(distance, 1),
        })

    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return candidates[:top_n]

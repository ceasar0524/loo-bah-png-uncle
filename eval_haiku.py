#!/usr/bin/env python3
"""
Haiku-only 店家辨識評估。
一次 Haiku call 同時做分類 + 特徵提取，再用本地規則比對 store_notes。
基準：CLIP-only 48.3%

用法：
    python eval_haiku.py [--photos ./photos] [--store-notes ./data/store_notes.json] [--no-cache]
"""
import argparse
import base64
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

_CACHE_FILE = Path("haiku_features_cache.json")

_PROMPT = """\
Look at this image and analyze it.

Return JSON only, no other text:
{
  "is_lu_rou_fan": "yes" or "no",
  "confidence": integer 0-10,
  "bowl_color": one of "bright_green" (vivid neon green) | "olive_green" (dark muted green) | "light_gray_green" (pale green-gray) | "white" | "yellow" | "red" | "black" | "brown" | "other",
  "bowl_shape": one of "round_bowl" | "wide_flat_plate" | "rectangular_box" | "other",
  "bowl_texture": one of "matte_ceramic" | "glossy_ceramic" | "plastic" | "styrofoam" | "other",
  "toppings": array from ["cilantro", "braised_egg", "soft_boiled_egg", "pork_floss", "pickled_radish", "green_onion", "cucumber"],
  "pork_part": one of "belly" (pork belly chunks, layered fat and lean) | "fatty" (mostly fat, little lean) | "lean" (mostly lean minced) | "skin_heavy" (lots of gelatinous pork skin),
  "fat_ratio": one of "fat_heavy" | "balanced" | "lean_heavy",
  "skin": one of "with_skin" (visible pork skin) | "no_skin",
  "sauce_color": one of "light" (pale golden-brown) | "medium" (medium brown) | "dark" (deep dark brown) | "black_gold" (black caramelized),
  "rice_quality": one of "fluffy" (separated grains) | "soft" (slightly sticky) | "mushy" (very soft overcooked)
}

Be precise about bowl color. Only include toppings clearly visible in the photo.
"""

_SUPPORTED = {".jpg", ".jpeg", ".png"}


def _pil_to_b64(pil_image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    return base64.standard_b64encode(buf.getvalue()).decode()


def extract_features(pil_image) -> dict:
    """一次 Haiku call：分類 + 特徵提取。"""
    import anthropic
    client = anthropic.Anthropic()
    img_b64 = _pil_to_b64(pil_image)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                {"type": "text", "text": _PROMPT},
            ],
        }],
    )

    raw = message.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {
            "is_lu_rou_fan": "no", "confidence": 0,
            "bowl_color": "other", "bowl_shape": "other",
            "bowl_texture": "other", "toppings": [],
        }


def match_store(features: dict, store_notes: dict) -> tuple:
    """本地規則：從特徵比對 store_notes，回傳 (predicted_store, score)。"""
    bowl_color = features.get("bowl_color", "other")
    bowl_shape = features.get("bowl_shape", "other")
    bowl_texture = features.get("bowl_texture", "other")
    toppings = set(features.get("toppings", []))

    scores: dict[str, float] = {}

    for store_name, data in store_notes.items():
        score = 0.0
        bowl = data.get("bowl", {})

        # 碗的特徵（高權重，視覺最明顯）
        if bowl.get("distinctive"):
            if bowl.get("color") == bowl_color:
                score += 0.5
            if bowl.get("shape") == bowl_shape:
                score += 0.2
            if bowl.get("texture") and bowl["texture"] == bowl_texture:
                score += 0.3

        # 特殊配料
        known_toppings = set(data.get("known_toppings", []))
        for t in known_toppings & toppings:
            score += 0.8 if t == "cilantro" else 0.3

        # visual_profile 比對（肉型、醬汁、豬皮）
        vp = data.get("visual_profile", {})
        if vp:
            if vp.get("pork_part") == features.get("pork_part"):
                score += 0.2
            if vp.get("sauce_color") == features.get("sauce_color"):
                score += 0.2
            if vp.get("skin") == features.get("skin"):
                score += 0.1
            if vp.get("fat_ratio") == features.get("fat_ratio"):
                score += 0.1

        if score > 0:
            scores[store_name] = score

    if not scores:
        return None, 0.0

    max_score = max(scores.values())
    tied = [s for s, v in scores.items() if max_score - v < 0.05]

    if len(tied) > 1:
        return None, max_score  # 平手

    return max(scores, key=scores.get), max_score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photos", default="./photos")
    parser.add_argument("--store-notes", default="./data/store_notes.json")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    photos_root = Path(args.photos)
    sys.path.insert(0, str(Path(__file__).parent))
    from src.preprocessing import preprocess

    with open(args.store_notes, encoding="utf-8") as f:
        store_notes = json.load(f)

    # 載入快取
    cache = {}
    if _CACHE_FILE.exists() and not args.no_cache:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        print(f"載入快取：{len(cache)} 筆")

    store_dirs = sorted([d for d in photos_root.iterdir() if d.is_dir()])
    all_photos = [
        (d.name, p)
        for d in store_dirs
        for p in sorted(d.iterdir())
        if p.suffix.lower() in _SUPPORTED
    ]
    print(f"共 {len(all_photos)} 張照片\n")

    # 特徵提取（有快取則跳過 API call）
    features_map: dict[str, dict] = {}
    new_entries = 0

    for store_name, img_path in all_photos:
        key = f"{store_name}/{img_path.name}"
        if key in cache:
            features_map[key] = cache[key]
        else:
            print(f"  Haiku: {key}...", flush=True)
            pil_img = preprocess(img_path)
            if pil_img is None:
                features_map[key] = None
                continue
            features = extract_features(pil_img)
            features_map[key] = features
            cache[key] = features
            new_entries += 1

    if new_entries > 0:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"\n快取已更新（+{new_entries} 筆）\n")

    # 評估
    correct = 0
    total = 0
    store_correct: dict[str, int] = defaultdict(int)
    store_total: dict[str, int] = defaultdict(int)
    confusion: dict[tuple, int] = defaultdict(int)
    no_match = 0

    for store_name, img_path in all_photos:
        key = f"{store_name}/{img_path.name}"
        features = features_map.get(key)
        if features is None:
            continue

        store_total[store_name] += 1
        total += 1

        conf = features.get("confidence", 0) / 10.0
        if features.get("is_lu_rou_fan") != "yes" or conf < 0.5:
            confusion[(store_name, "（非魯肉飯）")] += 1
            continue

        predicted, score = match_store(features, store_notes)

        if predicted is None:
            no_match += 1
            confusion[(store_name, "（無特徵）")] += 1
        elif predicted == store_name:
            correct += 1
            store_correct[store_name] += 1
        else:
            confusion[(store_name, predicted)] += 1

    # 輸出結果
    overall_acc = correct / total * 100 if total > 0 else 0
    print(f"\n{'='*55}")
    print(f"Haiku-only 辨識率：{correct}/{total} = {overall_acc:.1f}%")
    print(f"（{no_match} 張無特徵無法辨識 | CLIP-only 基準：48.3%）")
    print(f"{'='*55}")

    print("\n各店辨識率（由低到高）：")
    store_accs = []
    for store in sorted(store_total.keys()):
        t = store_total[store]
        c = store_correct[store]
        store_accs.append((c / t * 100 if t > 0 else 0, store, c, t))
    for acc, store, c, t in sorted(store_accs):
        print(f"  {store}: {c}/{t} = {acc:.1f}%")

    if confusion:
        print("\n混淆摘要（前 10）：")
        for (true_s, pred_s), cnt in sorted(confusion.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {true_s} → {pred_s}：{cnt} 次")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hybrid CLIP + Haiku 店家辨識評估。
CLIP KNN 為主要信號；Haiku 偵測到高信心明確特徵時才覆蓋 CLIP 結果。
基準：CLIP-only 48.3%，Haiku-only 見 eval_haiku.py

用法：
    python eval_hybrid.py [--photos ./photos] [--store-notes ./data/store_notes.json] [--k 5] [--no-cache]
"""
import argparse
import base64
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

_CACHE_FILE = Path("haiku_features_cache.json")
_SUPPORTED = {".jpg", ".jpeg", ".png"}

# Haiku 特徵覆蓋門檻：達到此分數才覆蓋 CLIP 結果
_HAIKU_OVERRIDE_THRESHOLD = 0.75

# 特徵分數（累加後與門檻比較）
_BOWL_COLOR_SCORE = 0.5
_BOWL_SHAPE_SCORE = 0.2
_BOWL_TEXTURE_SCORE = 0.3
_CILANTRO_SCORE = 0.8
_TOPPING_SCORE = 0.3

# CLIP 平手判定門檻
_TIE_MARGIN = 0.15

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


def _pil_to_b64(pil_image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    return base64.standard_b64encode(buf.getvalue()).decode()


def extract_features(pil_image) -> dict:
    """一次 Haiku call：分類 + 特徵提取（共用快取）。"""
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


def haiku_override(features: dict, store_notes: dict) -> tuple[str | None, float]:
    """
    Haiku 特徵比對：只有高信心時才回傳覆蓋建議，否則回傳 None。
    - 若同時有多家店達到門檻（平手），回傳 None（交給 CLIP）
    - 只有單一明確勝出時才覆蓋
    """
    bowl_color = features.get("bowl_color", "other")
    bowl_shape = features.get("bowl_shape", "other")
    bowl_texture = features.get("bowl_texture", "other")
    toppings = set(features.get("toppings", []))

    scores: dict[str, float] = {}

    for store_name, data in store_notes.items():
        score = 0.0
        bowl = data.get("bowl", {})
        if bowl.get("distinctive"):
            if bowl.get("color") == bowl_color:
                score += _BOWL_COLOR_SCORE
            if bowl.get("shape") == bowl_shape:
                score += _BOWL_SHAPE_SCORE
            if bowl.get("texture") and bowl["texture"] == bowl_texture:
                score += _BOWL_TEXTURE_SCORE

        known_toppings = set(data.get("known_toppings", []))
        for t in known_toppings & toppings:
            score += _CILANTRO_SCORE if t == "cilantro" else _TOPPING_SCORE

        if score >= _HAIKU_OVERRIDE_THRESHOLD:
            scores[store_name] = score

    if not scores:
        return None, 0.0

    max_score = max(scores.values())
    # 若有多家店都達標（平手），不覆蓋
    tied = [s for s, v in scores.items() if max_score - v < 0.05]
    if len(tied) > 1:
        return None, 0.0

    return max(scores, key=scores.get), max_score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photos", default="./photos")
    parser.add_argument("--store-notes", default="./data/store_notes.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    photos_root = Path(args.photos)
    sys.path.insert(0, str(Path(__file__).parent))

    import clip
    import numpy as np
    import torch
    from src.preprocessing import preprocess

    with open(args.store_notes, encoding="utf-8") as f:
        store_notes = json.load(f)

    # 載入快取
    cache = {}
    if _CACHE_FILE.exists() and not args.no_cache:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        print(f"載入快取：{len(cache)} 筆")

    # 載入 CLIP
    print("載入 CLIP 模型...")
    model, clip_preprocess = clip.load("ViT-B/32", device="cpu")
    model.eval()

    def embed(pil_img):
        tensor = clip_preprocess(pil_img).unsqueeze(0)
        with torch.no_grad():
            feat = model.encode_image(tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.squeeze().numpy().astype("float32")

    store_dirs = sorted([d for d in photos_root.iterdir() if d.is_dir()])
    all_photos = [
        (d.name, p)
        for d in store_dirs
        for p in sorted(d.iterdir())
        if p.suffix.lower() in _SUPPORTED
    ]
    print(f"共 {len(all_photos)} 張照片\n")

    # 產生 CLIP embedding + 提取 Haiku 特徵（有快取則跳過）
    all_vectors = []
    all_labels = []
    features_list = []
    photo_counts: dict[str, int] = defaultdict(int)
    new_entries = 0

    for store_name, img_path in all_photos:
        pil_img = preprocess(img_path)
        if pil_img is None:
            continue

        vec = embed(pil_img)
        all_vectors.append(vec)
        all_labels.append(store_name)
        photo_counts[store_name] += 1

        key = f"{store_name}/{img_path.name}"
        if key in cache:
            features_list.append(cache[key])
        else:
            print(f"  Haiku: {key}...", flush=True)
            features = extract_features(pil_img)
            features_list.append(features)
            cache[key] = features
            new_entries += 1

    if new_entries > 0:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"\n快取已更新（+{new_entries} 筆）\n")

    all_vectors_np = np.stack(all_vectors)
    total = len(all_labels)
    photo_counts = dict(photo_counts)

    print(f"開始 leave-one-out 評估（共 {total} 張，K={args.k}）...\n")

    correct_clip = 0
    correct_hybrid = 0
    store_correct_clip: dict[str, int] = defaultdict(int)
    store_correct_hybrid: dict[str, int] = defaultdict(int)
    store_total: dict[str, int] = defaultdict(int)
    confusion_hybrid: dict[tuple, int] = defaultdict(int)

    for i in range(total):
        true_store = all_labels[i]
        query_vec = all_vectors_np[i]
        feat = features_list[i]

        # CLIP leave-one-out index
        mask = np.ones(total, dtype=bool)
        mask[i] = False
        tmp_vectors = all_vectors_np[mask]
        tmp_labels = [all_labels[j] for j in range(total) if j != i]
        tmp_counts: dict[str, int] = defaultdict(int)
        for lbl in tmp_labels:
            tmp_counts[lbl] += 1

        # CLIP 正規化票數
        sims = tmp_vectors @ query_vec
        k = min(args.k, len(sims))
        top_idx = np.argpartition(sims, -k)[-k:]
        top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]

        store_votes: dict[str, int] = defaultdict(int)
        store_sims: dict[str, list] = defaultdict(list)
        for idx in top_idx:
            s = tmp_labels[idx]
            store_votes[s] += 1
            store_sims[s].append(float(sims[idx]))

        clip_norm: dict[str, float] = {
            s: v / max(tmp_counts.get(s, 1), 1)
            for s, v in store_votes.items()
        }

        # --- CLIP-only 預測（基準） ---
        if clip_norm:
            max_clip = max(clip_norm.values())
            clip_tied = [s for s, v in clip_norm.items() if max_clip - v <= _TIE_MARGIN]
            if len(clip_tied) == 1:
                avg_sim = float(np.mean(store_sims[clip_tied[0]]))
                clip_pred = clip_tied[0] if avg_sim >= 0.5 else None
            else:
                clip_pred = None
        else:
            clip_pred = None

        # --- Hybrid 預測：CLIP 為主，Haiku 高信心時覆蓋 ---
        haiku_pred_store, haiku_conf = haiku_override(feat, store_notes)

        if haiku_pred_store is not None:
            # Haiku 有高信心的明確特徵 → 覆蓋 CLIP
            hybrid_pred = haiku_pred_store
        else:
            # Haiku 無明確特徵 → 沿用 CLIP 結果
            hybrid_pred = clip_pred

        store_total[true_store] += 1

        if clip_pred == true_store:
            correct_clip += 1
            store_correct_clip[true_store] += 1

        if hybrid_pred == true_store:
            correct_hybrid += 1
            store_correct_hybrid[true_store] += 1
        else:
            confusion_hybrid[(true_store, hybrid_pred)] += 1

    # 輸出結果
    clip_acc = correct_clip / total * 100
    hybrid_acc = correct_hybrid / total * 100
    delta = hybrid_acc - clip_acc

    print(f"{'='*55}")
    print(f"CLIP-only  辨識率：{correct_clip}/{total} = {clip_acc:.1f}%")
    print(f"Hybrid     辨識率：{correct_hybrid}/{total} = {hybrid_acc:.1f}%  ({delta:+.1f}%)")
    print(f"{'='*55}")

    print("\n各店辨識率比較（由 Hybrid 由低到高）：")
    store_accs = []
    for store in sorted(store_total.keys()):
        t = store_total[store]
        cc = store_correct_clip[store]
        ch = store_correct_hybrid[store]
        store_accs.append((ch / t * 100 if t > 0 else 0, store, cc, ch, t))
    for h_acc, store, cc, ch, t in sorted(store_accs):
        clip_a = cc / t * 100 if t > 0 else 0
        delta_s = h_acc - clip_a
        print(f"  {store}: CLIP {cc}/{t}={clip_a:.0f}% → Hybrid {ch}/{t}={h_acc:.0f}% ({delta_s:+.0f}%)")

    if confusion_hybrid:
        print("\n混淆摘要（Hybrid，前 10）：")
        for (true_s, pred_s), cnt in sorted(confusion_hybrid.items(), key=lambda x: x[1], reverse=True)[:10]:
            pred_label = pred_s if pred_s else "（平手/未辨識）"
            print(f"  {true_s} → {pred_label}：{cnt} 次")


if __name__ == "__main__":
    main()

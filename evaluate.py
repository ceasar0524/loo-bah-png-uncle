#!/usr/bin/env python3
"""
Leave-one-out evaluation：量測 KNN 店家辨識率。

用法：
    python evaluate.py --photos ./photos [--k 5] [--threshold 0.5]
"""
import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def main():
    parser = argparse.ArgumentParser(description="KNN 店家辨識率評估（leave-one-out）")
    parser.add_argument("--photos", required=True, help="店家照片根目錄（每家店一個子目錄）")
    parser.add_argument("--k", type=int, default=5, help="KNN 的 K 值（預設：5）")
    parser.add_argument("--threshold", type=float, default=0.5, help="相似度門檻（預設：0.5）")
    args = parser.parse_args()

    photos_root = Path(args.photos)
    if not photos_root.is_dir():
        print(f"錯誤：找不到照片目錄「{args.photos}」")
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    import clip
    import numpy as np
    import torch
    from PIL import Image

    from src.preprocessing import preprocess
    from src.store_matching import match_store

    _SUPPORTED = {".jpg", ".jpeg", ".png"}
    _MODEL_NAME = "ViT-B/32"

    # ------------------------------------------------------------------ #
    # 載入 CLIP 模型
    # ------------------------------------------------------------------ #
    print("載入 CLIP 模型...")
    model, clip_preprocess = clip.load(_MODEL_NAME, device="cpu")
    model.eval()

    def embed(pil_img):
        tensor = clip_preprocess(pil_img).unsqueeze(0)
        with torch.no_grad():
            feat = model.encode_image(tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.squeeze().numpy().astype("float32")

    # ------------------------------------------------------------------ #
    # 收集所有照片的向量與標籤
    # ------------------------------------------------------------------ #
    print("讀取照片並產生 embedding...")
    store_dirs = sorted([d for d in photos_root.iterdir() if d.is_dir()])
    if not store_dirs:
        print("錯誤：目錄下沒有店家子目錄")
        sys.exit(1)

    all_vectors = []
    all_labels = []
    photo_counts = {}

    for store_dir in store_dirs:
        store_name = store_dir.name
        count = 0
        for img_path in sorted(store_dir.iterdir()):
            if img_path.suffix.lower() not in _SUPPORTED:
                continue
            pil_img = preprocess(img_path)
            if pil_img is None:
                continue
            vec = embed(pil_img)
            all_vectors.append(vec)
            all_labels.append(store_name)
            count += 1
        if count > 0:
            photo_counts[store_name] = count
            print(f"  {store_name}: {count} 張")
        else:
            print(f"  {store_name}: 沒有可用照片，跳過")

    if not all_vectors:
        print("錯誤：沒有任何照片可以評估")
        sys.exit(1)

    all_vectors = np.stack(all_vectors)
    total = len(all_labels)

    # ------------------------------------------------------------------ #
    # Leave-one-out 評估
    # ------------------------------------------------------------------ #
    print(f"\n開始 leave-one-out 評估（共 {total} 張，K={args.k}）...")

    correct = 0
    store_correct = defaultdict(int)
    store_total = defaultdict(int)
    confusion = defaultdict(int)  # (true, predicted) -> count

    for i in range(total):
        true_store = all_labels[i]
        query_vec = all_vectors[i]

        # 建立不含第 i 張的臨時索引
        mask = np.ones(total, dtype=bool)
        mask[i] = False
        tmp_vectors = all_vectors[mask]
        tmp_labels = [all_labels[j] for j in range(total) if j != i]

        # 重算臨時 photo_counts（排除第 i 張）
        tmp_counts = defaultdict(int)
        for lbl in tmp_labels:
            tmp_counts[lbl] += 1

        tmp_index = {
            "vectors": tmp_vectors,
            "labels": tmp_labels,
            "photo_counts": dict(tmp_counts),
        }

        result = match_store(query_vec, tmp_index, k=args.k, threshold=args.threshold)

        store_total[true_store] += 1

        if result["is_tie"] or not result["matches"]:
            predicted = None
        else:
            predicted = result["matches"][0]["store_name"]

        if predicted == true_store:
            correct += 1
            store_correct[true_store] += 1
        else:
            confusion[(true_store, predicted)] += 1

    # ------------------------------------------------------------------ #
    # 輸出結果
    # ------------------------------------------------------------------ #
    overall_acc = correct / total * 100
    print(f"\n{'='*50}")
    print(f"整體辨識率：{correct}/{total} = {overall_acc:.1f}%")
    print(f"{'='*50}")

    # 各店辨識率，由低到高排列
    print("\n各店辨識率（由低到高）：")
    store_accs = []
    for store in sorted(photo_counts.keys()):
        t = store_total[store]
        c = store_correct[store]
        acc = c / t * 100 if t > 0 else 0.0
        store_accs.append((acc, store, c, t))
    store_accs.sort()
    for acc, store, c, t in store_accs:
        print(f"  {store}: {c}/{t} = {acc:.1f}%")

    # 混淆摘要
    if confusion:
        print("\n最常混淆的組合：")
        sorted_conf = sorted(confusion.items(), key=lambda x: x[1], reverse=True)
        for (true_s, pred_s), cnt in sorted_conf[:10]:
            pred_label = pred_s if pred_s else "（未辨識）"
            print(f"  {true_s} → 預測為 {pred_label}：{cnt} 次")
    else:
        print("\n沒有混淆記錄（全部正確！）")


if __name__ == "__main__":
    main()

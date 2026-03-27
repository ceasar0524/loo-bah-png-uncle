"""
向量索引建立模組。
掃描店家照片目錄，使用 CLIP 產生 embedding，儲存為 .npz 供 store-matching 使用。
"""
import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional

import clip
import numpy as np
import torch

from src.preprocessing import preprocess

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}
_CLIP_MODEL_NAME = "ViT-B/32"

# 全域快取模型，避免重複載入
_model = None
_clip_preprocess = None


def _get_model():
    global _model, _clip_preprocess
    if _model is None:
        device = "cpu"
        _model, _clip_preprocess = clip.load(_CLIP_MODEL_NAME, device=device)
        _model.eval()
    return _model, _clip_preprocess


def _embed(pil_image, model, clip_preprocess) -> Optional[np.ndarray]:
    """將 PIL Image 轉為 CLIP 向量（L2 正規化）。"""
    try:
        tensor = clip_preprocess(pil_image).unsqueeze(0)
        with torch.no_grad():
            features = model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze().numpy().astype(np.float32)
    except Exception as e:
        logger.warning("Embedding failed: %s", e)
        return None


def build_index(photos_dir: str, output_path: str) -> dict:
    """
    掃描照片目錄，建立向量索引並儲存為 .npz。

    目錄結構：
        photos_dir/
            店家A/
                photo1.jpg
                photo2.jpg
            店家B/
                ...

    Args:
        photos_dir: 包含各店家子目錄的根目錄路徑
        output_path: 索引輸出路徑（.npz）

    Returns:
        {'stores': int, 'photos': int} 建立摘要
    """
    root = Path(photos_dir)
    if not root.is_dir():
        raise ValueError(f"找不到照片目錄：{photos_dir}")

    model, clip_preprocess = _get_model()

    vectors = []
    labels = []
    photo_counts = {}

    store_dirs = sorted([d for d in root.iterdir() if d.is_dir()])
    if not store_dirs:
        raise ValueError(f"目錄下沒有店家子目錄：{photos_dir}")

    for store_dir in store_dirs:
        store_name = store_dir.name
        count = 0

        for img_path in sorted(store_dir.iterdir()):
            if img_path.suffix.lower() not in _SUPPORTED_SUFFIXES:
                logger.warning("Unsupported format skipped: %s", img_path)
                continue

            pil_img = preprocess(img_path)
            if pil_img is None:
                continue

            vec = _embed(pil_img, model, clip_preprocess)
            if vec is None:
                continue

            vectors.append(vec)
            labels.append(store_name)
            count += 1

        if count > 0:
            photo_counts[store_name] = count
            logger.info("  %s: %d 張", store_name, count)
        else:
            logger.warning("  %s: 沒有可處理的照片，跳過", store_name)

    if not vectors:
        raise ValueError("沒有任何照片可以建立索引")

    vectors_arr = np.stack(vectors)
    labels_arr = np.array(labels)
    store_names = np.array(list(photo_counts.keys()))
    counts_arr = np.array([photo_counts[s] for s in store_names])

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output,
        vectors=vectors_arr,
        labels=labels_arr,
        store_names=store_names,
        photo_counts=counts_arr,
    )

    summary = {"stores": len(photo_counts), "photos": len(vectors)}
    print(f"✓ 索引建立完成：{summary['stores']} 家店，{summary['photos']} 張照片 → {output_path}")
    return summary


def load_index(index_path: str) -> dict:
    """
    載入 .npz 索引檔。

    Returns:
        {
            'vectors': np.ndarray (N, D),
            'labels': np.ndarray (N,),
            'photo_counts': dict {store_name: count}
        }
    """
    path = Path(index_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到索引檔：{index_path}")

    data = np.load(path, allow_pickle=False)
    store_names = data["store_names"].tolist()
    counts = data["photo_counts"].tolist()
    photo_counts = dict(zip(store_names, counts))

    return {
        "vectors": data["vectors"],
        "labels": data["labels"].tolist(),
        "photo_counts": photo_counts,
    }

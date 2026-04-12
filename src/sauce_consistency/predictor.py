"""
DINOv2 醬汁濃稠度預測模組。
使用 center-crop embedding + KNN 投票，比對 index_sauce_crop.npz 中的 reference embeddings。
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_DEFAULT_INDEX_PATH = Path(__file__).parent.parent.parent / "index_sauce_crop.npz"
_DEFAULT_K = 5

# process 層級快取（lazy init）
_model = None
_transform = None


def _get_model_and_transform():
    global _model, _transform
    if _model is None:
        try:
            import torch
            from torchvision import transforms

            logger.info("載入 DINOv2 模型（dinov2_vitb14）...")
            _model = torch.hub.load(
                "facebookresearch/dinov2", "dinov2_vitb14", verbose=False
            )
            _model.eval()
            _transform = transforms.Compose([
                transforms.Resize(256, interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225]),
            ])
        except Exception as e:
            logger.warning("DINOv2 模型載入失敗：%s", e)
            _model = None
            _transform = None
    return _model, _transform


def _embed(pil_img) -> Optional[np.ndarray]:
    """將 PIL image 轉為 DINOv2 embedding（已 L2 正規化）。"""
    model, transform = _get_model_and_transform()
    if model is None or transform is None:
        return None
    try:
        import torch
        tensor = transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            feat = model(tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.squeeze().numpy().astype("float32")
    except Exception as e:
        logger.warning("DINOv2 embedding 失敗：%s", e)
        return None


def predict_consistency(
    pil_img,
    index_path: Optional[str] = None,
    k: int = _DEFAULT_K,
) -> Optional[tuple[str, float]]:
    """
    預測 query 圖片的醬汁濃稠類別（稠 / 水）及信心度。

    Args:
        pil_img:     PIL Image（已前處理）
        index_path:  sauce crop reference index 路徑（.npz）；None 則使用預設路徑
        k:           KNN 鄰居數，預設 5

    Returns:
        (label, confidence)：label 為 "稠" 或 "水"，confidence 介於 0.5～1.0；
        預測失敗時回傳 None
    """
    idx_path = Path(index_path) if index_path else _DEFAULT_INDEX_PATH
    if not idx_path.exists():
        logger.warning("sauce crop index 不存在：%s，跳過濃稠度預測", idx_path)
        return None

    query_vec = _embed(pil_img)
    if query_vec is None:
        return None

    try:
        data = np.load(str(idx_path), allow_pickle=True)
        vectors: np.ndarray = data["vectors"]   # (N, D)
        labels = data["labels"].tolist()         # (N,) — "稠" or "水"
    except Exception as e:
        logger.warning("載入 sauce crop index 失敗：%s", e)
        return None

    # 計算各類別總數（正規化基準）
    class_counts: dict[str, int] = {}
    for lbl in labels:
        if lbl in ("稠", "水"):
            class_counts[lbl] = class_counts.get(lbl, 0) + 1

    sims = vectors @ query_vec
    actual_k = min(k, len(sims))
    top_idx = np.argpartition(sims, -actual_k)[-actual_k:]

    raw_votes: dict[str, int] = {}
    for i in top_idx:
        label = labels[i]
        if label in ("稠", "水"):
            raw_votes[label] = raw_votes.get(label, 0) + 1

    if not raw_votes:
        logger.warning("DINOv2 KNN 無有效投票，回傳 None")
        return None

    # 正規化：raw votes / class size，消除 class imbalance
    normalized = {
        lbl: raw_votes[lbl] / class_counts.get(lbl, 1)
        for lbl in raw_votes
    }
    total = sum(normalized.values())
    winner = max(normalized, key=normalized.get)
    confidence = normalized[winner] / total if total > 0 else 0.0
    return winner, confidence

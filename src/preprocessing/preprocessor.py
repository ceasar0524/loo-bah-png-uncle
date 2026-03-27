"""
共用前處理模組。
store-embedding-db 和 visual-recognition 都呼叫此模組，確保前處理一致。
"""
import logging
import warnings
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_MAX_SIZE = 1024
_CLAHE_CLIP_LIMIT = 2.0
_CLAHE_TILE_GRID_SIZE = 8
_SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}


def preprocess(source: Union[str, Path, Image.Image]) -> Optional[Image.Image]:
    """
    對輸入圖片套用前處理管線：resize（最大 1024px）+ 亮度正規化（CLAHE）。

    Args:
        source: 圖片路徑（str 或 Path）或已開啟的 PIL Image。

    Returns:
        前處理後的 PIL Image（RGB），若無法讀取或格式不支援則回傳 None。
        結果不寫入磁碟。
    """
    img = _load(source)
    if img is None:
        return None
    img = _resize(img)
    img = _apply_clahe(img)
    return img


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load(source: Union[str, Path, Image.Image]) -> Optional[Image.Image]:
    if isinstance(source, Image.Image):
        return source.convert("RGB")

    path = Path(source)

    if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
        logger.warning("Unsupported format skipped: %s", path)
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            img = Image.open(path)
            img.verify()          # 偵測損壞的檔案
        img = Image.open(path).convert("RGB")  # verify 後需重新開啟
        return img
    except Exception as e:
        logger.warning("Corrupted image skipped: %s (%s)", path, e)
        return None


def _resize(img: Image.Image) -> Image.Image:
    """長邊超過 1024px 才縮放，小圖不放大。"""
    w, h = img.size
    longest = max(w, h)
    if longest <= _MAX_SIZE:
        return img
    scale = _MAX_SIZE / longest
    new_w = int(w * scale)
    new_h = int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


def _apply_clahe(img: Image.Image) -> Image.Image:
    """對 LAB 色彩空間的 L 通道做 CLAHE 亮度正規化。"""
    arr = np.array(img, dtype=np.uint8)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=_CLAHE_CLIP_LIMIT,
        tileGridSize=(_CLAHE_TILE_GRID_SIZE, _CLAHE_TILE_GRID_SIZE),
    )
    l_eq = clahe.apply(l)

    lab_eq = cv2.merge([l_eq, a, b])
    rgb = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)
    return Image.fromarray(rgb)

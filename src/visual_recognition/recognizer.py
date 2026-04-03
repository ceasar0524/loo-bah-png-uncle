"""
visual_recognition 整合模組。
對輸入圖片先分類是否為魯肉飯，確認後再辨識各項特徵。
"""
import logging
from typing import Optional, Union
from pathlib import Path

from src import clip_model
from src.preprocessing import preprocess
from src.schemas import VisualResult
from src.visual_recognition.classifier import classify
from src.visual_recognition.feature_recognizer import recognize_features

logger = logging.getLogger(__name__)


def recognize(
    source: Union[str, Path, "PIL.Image.Image"],
    threshold: float = 0.6,
) -> VisualResult:
    """
    辨識照片是否為魯肉飯，並擷取各項視覺特徵。

    Args:
        source: 圖片路徑或 PIL Image（未前處理皆可，內部會呼叫 preprocess）
        threshold: 判定為魯肉飯的 CLIP 信心門檻（預設 0.6）

    Returns:
        VisualResult TypedDict
    """
    from PIL import Image

    if isinstance(source, Image.Image):
        pil_img = source
    else:
        pil_img = preprocess(source)
        if pil_img is None:
            logger.warning("preprocess failed for %s", source)
            return _empty_result(0.0)

    # 取得圖片向量（共用 CLIP singleton）
    img_feat = clip_model.encode_image(pil_img)  # (1, D)

    # 魯肉飯判斷 + 碗特徵提取（單次 Haiku call）
    is_lrf, confidence, clf_features = classify(pil_img, threshold=threshold)

    if not is_lrf:
        return _empty_result(confidence, clf_features.get("food_type", "other"))

    return VisualResult(
        is_lu_rou_fan=True,
        food_type="lu_rou_fan",
        confidence=confidence,
        toppings=clf_features.get("toppings", []),
        bowl_color=clf_features.get("bowl_color"),
        bowl_shape=clf_features.get("bowl_shape"),
        bowl_texture=clf_features.get("bowl_texture"),
        pork_part=clf_features.get("pork_part"),
        fat_ratio=clf_features.get("fat_ratio"),
        skin=clf_features.get("skin"),
        sauce_color=clf_features.get("sauce_color"),
        rice_quality=clf_features.get("rice_quality"),
    )


def _empty_result(confidence: float, food_type: str = "other") -> VisualResult:
    return VisualResult(
        is_lu_rou_fan=False,
        food_type=food_type,
        confidence=confidence,
        toppings=[],
        bowl_color=None,
        bowl_shape=None,
        bowl_texture=None,
        pork_part=None,
        fat_ratio=None,
        skin=None,
        sauce_color=None,
        rice_quality=None,
    )

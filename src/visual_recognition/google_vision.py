"""
使用 Google Cloud Vision API 偵測魯肉飯配料。
用 label detection 識別照片中的食材，對應到配料 key。
"""
import io
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / "config"

_DEFAULT_TOPPINGS = [
    {"key": "cilantro", "name_zh": "香菜"},
    {"key": "braised_egg", "name_zh": "滷蛋"},
    {"key": "bamboo_shoots", "name_zh": "筍乾"},
    {"key": "tofu", "name_zh": "豆腐"},
    {"key": "pickled_mustard", "name_zh": "酸菜"},
    {"key": "soft_boiled_egg", "name_zh": "半熟荷包蛋"},
    {"key": "hard_boiled_egg", "name_zh": "全熟荷包蛋"},
    {"key": "oyster", "name_zh": "鮮蚵"},
    {"key": "pickled_radish", "name_zh": "醃黃蘿蔔"},
    {"key": "cucumber", "name_zh": "小黃瓜"},
    {"key": "pork_floss", "name_zh": "肉鬆"},
    {"key": "shredded_chicken", "name_zh": "雞肉絲"},
    {"key": "braised_cabbage", "name_zh": "魯白菜"},
    {"key": "green_onion", "name_zh": "蔥"},
    {"key": "fried_shallots", "name_zh": "炸紅蔥頭"},
]

# Google Vision label → topping key 對照表
# 每個 label 可以是字串（單一對應）或列表（多個候選，需進一步判斷）
_LABEL_MAP: dict[str, str] = {
    # 香菜
    "cilantro": "cilantro",
    "coriander": "cilantro",
    "chinese parsley": "cilantro",
    # 滷蛋
    "braised egg": "braised_egg",
    "soy egg": "braised_egg",
    "marinated egg": "braised_egg",
    "tea egg": "braised_egg",
    # 筍乾
    "bamboo shoot": "bamboo_shoots",
    "bamboo shoots": "bamboo_shoots",
    "dried bamboo": "bamboo_shoots",
    # 豆腐
    "tofu": "tofu",
    "bean curd": "tofu",
    "braised tofu": "tofu",
    # 酸菜
    "pickled mustard": "pickled_mustard",
    "mustard greens": "pickled_mustard",
    "preserved vegetable": "pickled_mustard",
    "sauerkraut": "pickled_mustard",
    # 半熟荷包蛋
    "fried egg": "soft_boiled_egg",
    "sunny side up": "soft_boiled_egg",
    "runny egg": "soft_boiled_egg",
    "soft boiled egg": "soft_boiled_egg",
    "poached egg": "soft_boiled_egg",
    # 全熟荷包蛋
    "hard boiled egg": "hard_boiled_egg",
    "hard-boiled egg": "hard_boiled_egg",
    # 鮮蚵
    "oyster": "oyster",
    "fresh oyster": "oyster",
    # 醃黃蘿蔔
    "pickled radish": "pickled_radish",
    "yellow radish": "pickled_radish",
    "daikon": "pickled_radish",
    "turnip": "pickled_radish",
    # 小黃瓜
    "cucumber": "cucumber",
    "sliced cucumber": "cucumber",
    # 肉鬆
    "pork floss": "pork_floss",
    "meat floss": "pork_floss",
    "rousong": "pork_floss",
    # 雞肉絲
    "shredded chicken": "shredded_chicken",
    "chicken": "shredded_chicken",
    # 魯白菜
    "cabbage": "braised_cabbage",
    "braised cabbage": "braised_cabbage",
    "napa cabbage": "braised_cabbage",
    # 蔥
    "green onion": "green_onion",
    "scallion": "green_onion",
    "spring onion": "green_onion",
    "chive": "green_onion",
    # 炸紅蔥頭
    "fried shallot": "fried_shallots",
    "fried shallots": "fried_shallots",
    "shallot": "fried_shallots",
    "crispy shallot": "fried_shallots",
}

# 最低信心門檻（Google Vision score）
_MIN_SCORE = 0.6


def _load_toppings() -> list:
    path = _CONFIG_DIR / "toppings.yaml"
    if not path.exists():
        return _DEFAULT_TOPPINGS
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("toppings", _DEFAULT_TOPPINGS)
    except Exception as e:
        logger.warning("Failed to load toppings.yaml: %s", e)
        return _DEFAULT_TOPPINGS


def _pil_to_bytes(pil_image) -> bytes:
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    return buf.getvalue()


def detect_toppings_google(pil_image) -> list[str]:
    """
    用 Google Cloud Vision API 偵測照片中的配料。
    使用 Application Default Credentials（gcloud auth application-default login）。

    Args:
        pil_image: 前處理後的 PIL Image

    Returns:
        偵測到的配料 key 列表
    """
    try:
        from google.cloud import vision
    except ImportError:
        logger.error("google-cloud-vision 未安裝，請執行 pip3 install google-cloud-vision")
        return []

    toppings_cfg = _load_toppings()
    valid_keys = {t["key"] for t in toppings_cfg}

    try:
        client = vision.ImageAnnotatorClient()
        image_bytes = _pil_to_bytes(pil_image)
        image = vision.Image(content=image_bytes)

        response = client.label_detection(image=image, max_results=30)

        if response.error.message:
            logger.warning("Google Vision API error: %s", response.error.message)
            return []

        detected = set()
        for label in response.label_annotations:
            label_text = label.description.lower()
            score = label.score

            if score < _MIN_SCORE:
                continue

            if label_text in _LABEL_MAP:
                key = _LABEL_MAP[label_text]
                if key in valid_keys:
                    detected.add(key)
                    logger.debug("Detected %s via label '%s' (score=%.2f)", key, label_text, score)

        return list(detected)

    except Exception as e:
        logger.warning("Google Vision topping detection failed: %s", e)
        return []

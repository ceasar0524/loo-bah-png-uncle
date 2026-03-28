"""
使用 Claude Vision 偵測魯肉飯配料。
比 CLIP zero-shot 更準確，特別是細小配料（香菜、蔥等）。
"""
import base64
import io
import logging
import os
from pathlib import Path

import anthropic
import yaml

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / "config"
_MODEL = "claude-haiku-4-5-20251001"

_REFERENCES_DIR = Path(__file__).parent / "config" / "references"

_DEFAULT_TOPPINGS = [
    {"key": "cilantro", "name_zh": "香菜"},
    {"key": "braised_egg", "name_zh": "滷蛋"},
    {"key": "tofu", "name_zh": "豆腐"},
    {"key": "pickled_mustard", "name_zh": "酸菜"},
    {"key": "soft_boiled_egg", "name_zh": "半熟荷包蛋"},
    {"key": "hard_boiled_egg", "name_zh": "全熟荷包蛋"},
    {"key": "oyster", "name_zh": "鮮蚵"},
    {"key": "pickled_radish", "name_zh": "醃黃蘿蔔"},
    {"key": "pickled_cucumber", "name_zh": "醃小黃瓜"},
    {"key": "yin_gua", "name_zh": "醬瓜"},
    {"key": "pork_floss", "name_zh": "肉鬆"},
    {"key": "shredded_chicken", "name_zh": "雞肉絲"},
    {"key": "braised_cabbage", "name_zh": "魯白菜"},
    {"key": "green_onion", "name_zh": "蔥"},
]


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


def _pil_to_base64(pil_image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def detect_toppings_vision(pil_image) -> list[str]:
    """
    用 Claude Vision 偵測照片中的配料。

    Args:
        pil_image: 前處理後的 PIL Image

    Returns:
        偵測到的配料 key 列表
    """
    toppings_cfg = _load_toppings()
    topping_names = "、".join(f"{t['name_zh']}（{t['key']}）" for t in toppings_cfg)

    prompt = f"""請仔細看這碗魯肉飯照片，判斷照片中清楚可見的配料。

可能出現的配料：
{topping_names}

只回答照片中確認看得到的配料 key（英文），用逗號分隔。如果都沒有，回答 none。不要解釋，只回答 key。"""

    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        img_b64 = _pil_to_base64(pil_image)

        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64},
            },
            {"type": "text", "text": prompt},
        ]

        message = client.messages.create(
            model=_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": content}],
        )

        raw = message.content[0].text.strip().lower()
        if raw == "none" or not raw:
            return []

        valid_keys = {t["key"] for t in toppings_cfg}
        detected = [k.strip() for k in raw.split(",") if k.strip() in valid_keys]
        return detected

    except Exception as e:
        logger.warning("Claude Vision topping detection failed: %s", e)
        return []

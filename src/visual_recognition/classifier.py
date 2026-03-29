"""
魯肉飯辨識分類器。
使用 Claude Haiku vision 判斷照片是否為魯肉飯，並於同一次 API call 提取視覺特徵。

判斷流程：
  1. 傳送圖片給 Claude Haiku，要求回傳 JSON（分類 + 視覺特徵）
  2. 將 0-10 信心值正規化為 0.0–1.0，與 threshold 比較
  3. 若為魯肉飯，回傳碗色、碗形、碗質感、配料等特徵
"""
import base64
import io
import json
import logging

import anthropic

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = 0.5

_client = anthropic.Anthropic()

_PROMPT = """\
Look at this image and analyze it.

Return JSON only, no other text:
{
  "is_lu_rou_fan": "yes" or "no",
  "confidence": integer 0-10,
  "bowl_color": one of "bright_green" (vivid neon green) | "olive_green" (dark muted green) | "light_gray_green" (pale green-gray) | "white" | "yellow" | "red" | "black" | "brown" | "silver" (stainless steel metallic) | "other",
  "bowl_shape": one of "round_bowl" | "wide_flat_plate" | "rectangular_box" | "other",
  "bowl_texture": one of "matte_ceramic" | "glossy_ceramic" | "plastic" | "styrofoam" | "metal" | "other",
  "toppings": array from ["cilantro", "braised_egg", "soft_boiled_egg", "pork_floss", "pickled_radish", "pickled_cucumber", "green_onion", "yin_gua"]
  (cilantro = fresh herb with flat jagged leaves and thin stems, leafy NOT sliced; pickled_radish = bright yellow pickled daikon slices placed directly on top of the rice; pickled_cucumber = bright green flat round cucumber slices, NOT leafy; yin_gua = dark brown soft braised melon chunks)
}

Lu rou fan typically has white rice in a bowl with braised pork (minced or belly chunks) and dark soy sauce.
Be precise about bowl color. Only include toppings clearly visible in the photo.
When is_lu_rou_fan is "no", still return bowl_color, bowl_shape, bowl_texture, and toppings fields.
"""

_FALLBACK = {
    "is_lu_rou_fan": "no",
    "confidence": 0,
    "bowl_color": None,
    "bowl_shape": None,
    "bowl_texture": None,
    "toppings": [],
}


def _pil_to_base64(pil_image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    return base64.standard_b64encode(buf.getvalue()).decode()


def classify(
    pil_image,
    threshold: float = _DEFAULT_THRESHOLD,
) -> tuple[bool, float, dict]:
    """
    判斷圖片是否為魯肉飯，並提取視覺特徵（單次 Haiku call）。

    Args:
        pil_image: 前處理後的 PIL Image
        threshold: 判定為魯肉飯的信心門檻（預設 0.5）

    Returns:
        (is_lu_rou_fan, confidence, features)
        - confidence 為 0.0–1.0
        - features 包含 bowl_color、bowl_shape、bowl_texture、toppings
          若非魯肉飯，bowl 欄位為 None，toppings 為空 list
    """
    img_b64 = _pil_to_base64(pil_image)

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw.strip())
    except (json.JSONDecodeError, ValueError):
        logger.warning("classify: JSON parse failed, using fallback")
        return False, 0.0, dict(_FALLBACK)

    score = int(data.get("confidence", 0))
    confidence = score / 10.0
    is_lu_rou_fan = data.get("is_lu_rou_fan") == "yes" and confidence >= threshold

    if is_lu_rou_fan:
        features = {
            "bowl_color": data.get("bowl_color"),
            "bowl_shape": data.get("bowl_shape"),
            "bowl_texture": data.get("bowl_texture"),
            "toppings": data.get("toppings", []),
        }
    else:
        features = {
            "bowl_color": None,
            "bowl_shape": None,
            "bowl_texture": None,
            "toppings": [],
        }

    logger.debug(
        "classify: is_lrf=%s confidence=%.2f threshold=%.2f bowl_color=%s toppings=%s",
        is_lu_rou_fan, confidence, threshold,
        features["bowl_color"], features["toppings"],
    )
    return is_lu_rou_fan, confidence, features

"""
魯肉飯特徵辨識器。
使用 CLIP zero-shot 辨識配料、肉的部位、肥瘦比例、豬皮、醬汁顏色、米飯品質。
所有類別從 YAML 設定檔載入，缺少設定檔時 fallback 到預設值。
"""
import logging
from pathlib import Path
from typing import Optional

import yaml

from src import clip_model

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / "config"

# ------------------------------------------------------------------ #
# 預設值（當設定檔不存在時使用）
# ------------------------------------------------------------------ #

_DEFAULT_TOPPINGS = [
    {"key": "cilantro", "name_en": "cilantro", "name_zh": "香菜"},
    {"key": "braised_egg", "name_en": "braised egg", "name_zh": "滷蛋"},
    {"key": "tofu", "name_en": "braised tofu", "name_zh": "豆腐"},
    {"key": "pickled_mustard", "name_en": "pickled mustard greens", "name_zh": "酸菜"},
    {"key": "soft_boiled_egg", "name_en": "soft boiled egg", "name_zh": "半熟荷包蛋"},
    {"key": "hard_boiled_egg", "name_en": "hard boiled egg", "name_zh": "全熟荷包蛋"},
    {"key": "oyster", "name_en": "fresh oyster", "name_zh": "鮮蚵"},
    {"key": "pickled_radish", "name_en": "pickled yellow radish", "name_zh": "醃黃蘿蔔"},
    {"key": "cucumber", "name_en": "sliced cucumber", "name_zh": "小黃瓜"},
    {"key": "pork_floss", "name_en": "pork floss", "name_zh": "肉鬆"},
    {"key": "shredded_chicken", "name_en": "shredded chicken", "name_zh": "雞肉絲"},
    {"key": "braised_cabbage", "name_en": "braised cabbage", "name_zh": "魯白菜"},
    {"key": "green_onion", "name_en": "green onion", "name_zh": "蔥"},
]

_DEFAULT_PORK_PARTS = [
    {"label": "belly", "prompt_en": "braised pork belly with alternating fat and lean layers", "prompt_zh": "五花肉，肥瘦相間的三層肉"},
    {"label": "fatty", "prompt_en": "braised pork with mostly fat, very little lean meat", "prompt_zh": "肥肉多，瘦肉少的滷肉"},
    {"label": "lean", "prompt_en": "braised pork with mostly lean meat, very little fat", "prompt_zh": "瘦肉多，肥肉少的滷肉"},
    {"label": "skin_heavy", "prompt_en": "braised pork with lots of gelatinous pork skin", "prompt_zh": "皮多，有大量豬皮的滷肉"},
]

_DEFAULT_FAT_RATIO = [
    {"label": "fat_heavy", "prompt_en": "braised pork rice with fat-heavy pork, ratio approximately 7 fat to 3 lean", "prompt_zh": "肥肉比例高的魯肉飯，約七分肥三分瘦"},
    {"label": "balanced", "prompt_en": "braised pork rice with balanced fat and lean, ratio approximately 5 to 5", "prompt_zh": "肥瘦均衡的魯肉飯，約五五比"},
    {"label": "lean_heavy", "prompt_en": "braised pork rice with lean-heavy pork, ratio approximately 3 fat to 7 lean", "prompt_zh": "瘦肉比例高的魯肉飯，約三分肥七分瘦"},
]

_DEFAULT_SKIN = [
    {"label": "with_skin", "prompt_en": "braised pork rice with visible gelatinous pork skin on top", "prompt_zh": "有豬皮的魯肉飯，看得到軟爛膠質豬皮"},
    {"label": "no_skin", "prompt_en": "braised pork rice without pork skin, only meat chunks", "prompt_zh": "沒有豬皮的魯肉飯，只有肉塊"},
]

_DEFAULT_SAUCE_COLORS = [
    {"label": "light", "prompt_en": "braised pork rice with light golden-brown sauce", "prompt_zh": "醬色淺褐的魯肉飯，醬汁顏色淡"},
    {"label": "medium", "prompt_en": "braised pork rice with medium brown sauce", "prompt_zh": "醬色中褐的魯肉飯，一般滷汁顏色"},
    {"label": "dark", "prompt_en": "braised pork rice with very dark brown sauce", "prompt_zh": "醬色深褐的魯肉飯，深色濃郁滷汁"},
    {"label": "black_gold", "prompt_en": "braised pork rice with black caramelized sauce", "prompt_zh": "黑金色醬汁的魯肉飯，焦糖化深黑色滷汁"},
]

_DEFAULT_RICE_QUALITIES = [
    {"label": "fluffy", "prompt_en": "braised pork rice with fluffy separated rice grains", "prompt_zh": "米粒鬆散分開的魯肉飯"},
    {"label": "soft", "prompt_en": "braised pork rice with soft slightly sticky rice", "prompt_zh": "米飯軟嫩帶點黏性的魯肉飯"},
    {"label": "mushy", "prompt_en": "braised pork rice with mushy overcooked rice", "prompt_zh": "米飯過爛糊化的魯肉飯"},
]

_TOPPING_DETECTION_THRESHOLD = 0.55


# ------------------------------------------------------------------ #
# YAML 載入工具
# ------------------------------------------------------------------ #

def _load_yaml(filename: str, key: str, default: list) -> list:
    path = _CONFIG_DIR / filename
    if not path.exists():
        logger.debug("Config not found: %s, using defaults", path)
        return default
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get(key, default)
    except Exception as e:
        logger.warning("Failed to load %s: %s, using defaults", path, e)
        return default


# ------------------------------------------------------------------ #
# 特徵辨識函式
# ------------------------------------------------------------------ #

def detect_toppings(img_feat) -> list[str]:
    """
    二元判斷每種配料的有/無。
    img_feat: 已正規化的圖片向量 (1, D)
    """
    toppings_cfg = _load_yaml("toppings.yaml", "toppings", _DEFAULT_TOPPINGS)
    detected = []

    for item in toppings_cfg:
        key = item["key"]
        name_en = item["name_en"]
        name_zh = item["name_zh"]
        desc_en = item.get("desc_en", name_en)
        desc_zh = item.get("desc_zh", name_zh)

        prompts_with = [
            f"a bowl of braised pork rice with {desc_en} on top",
            f"一碗有{desc_zh}的魯肉飯",
        ]
        prompts_without = [
            f"a bowl of braised pork rice without any {desc_en}",
            f"一碗沒有{desc_zh}的魯肉飯",
        ]

        feats_with = clip_model.encode_text(prompts_with)
        feats_without = clip_model.encode_text(prompts_without)

        sim_with = float((img_feat @ feats_with.T).max())
        sim_without = float((img_feat @ feats_without.T).max())

        import torch
        logits = torch.tensor([sim_with, sim_without]) * 100.0
        prob_with = float(logits.softmax(dim=0)[0])

        threshold = item.get("threshold", _TOPPING_DETECTION_THRESHOLD)
        if prob_with >= threshold:
            detected.append(key)

    return detected


def _classify_from_categories(img_feat, categories: list) -> str:
    """
    從類別清單中選出相似度最高的標籤。
    每個類別有 prompt_en + prompt_zh，各取最高相似度後 softmax 選勝者。
    """
    import torch

    best_sims = []
    labels = []
    for cat in categories:
        prompts = [cat["prompt_en"], cat["prompt_zh"]]
        feats = clip_model.encode_text(prompts)
        sim = float((img_feat @ feats.T).max())
        best_sims.append(sim)
        labels.append(cat["label"])

    logits = torch.tensor(best_sims) * 100.0
    winner_idx = int(logits.argmax())
    return labels[winner_idx]


def classify_pork_part(img_feat) -> str:
    cats = _load_yaml("pork_parts.yaml", "categories", _DEFAULT_PORK_PARTS)
    return _classify_from_categories(img_feat, cats)


def classify_fat_ratio(img_feat) -> str:
    cats = _load_yaml("fat_ratio.yaml", "categories", _DEFAULT_FAT_RATIO)
    return _classify_from_categories(img_feat, cats)


def classify_skin(img_feat) -> str:
    cats = _load_yaml("skin.yaml", "categories", _DEFAULT_SKIN)
    return _classify_from_categories(img_feat, cats)


def classify_sauce_color(img_feat) -> str:
    cats = _load_yaml("sauce_colors.yaml", "categories", _DEFAULT_SAUCE_COLORS)
    return _classify_from_categories(img_feat, cats)


def classify_rice_quality(img_feat) -> str:
    cats = _load_yaml("rice_qualities.yaml", "categories", _DEFAULT_RICE_QUALITIES)
    return _classify_from_categories(img_feat, cats)


def recognize_features(img_feat, pil_image=None) -> dict:
    """
    對確認為魯肉飯的圖片辨識所有特徵。
    img_feat: 已正規化的圖片向量 (1, D)
    pil_image: 原始 PIL Image，提供時用 Google Vision 做配料偵測（更準確）
    """
    if pil_image is not None:
        from src.visual_recognition.claude_vision import detect_toppings_vision
        toppings = detect_toppings_vision(pil_image)
    else:
        toppings = detect_toppings(img_feat)

    return {
        "toppings": toppings,
        "pork_part": classify_pork_part(img_feat),
        "fat_ratio": classify_fat_ratio(img_feat),
        "skin": classify_skin(img_feat),
        "sauce_color": classify_sauce_color(img_feat),
        "rice_quality": classify_rice_quality(img_feat),
    }

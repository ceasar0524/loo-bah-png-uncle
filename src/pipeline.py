"""
魯肉飯辨識器核心 pipeline。
封裝完整流程：image-preprocessing → visual-recognition → store-matching → uncle-persona。
可被 CLI（recognize.py）或 Line Bot 等其他入口直接 import 使用。
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional, Union

from src.preprocessing import preprocess
from src.visual_recognition import recognize as visual_recognize
from src.store_matching import match_store
from src.store_embedding_db import load_index
from src.uncle_persona.persona import UnclePersona
from src.schemas import MatchingResult

logger = logging.getLogger(__name__)

_DEFAULT_STORE_NOTES = Path(__file__).parent.parent / "data" / "store_notes.json"

_persona = None


def _get_persona() -> UnclePersona:
    global _persona
    if _persona is None:
        _persona = UnclePersona()
    return _persona


def run(
    image_source: Union[str, Path],
    index_path: Optional[str] = None,
    threshold: float = 0.6,
    store_notes_path: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """
    執行完整辨識 pipeline，回傳大叔回應字串與辨識到的店家名稱。

    Args:
        image_source:      圖片路徑
        index_path:        向量索引路徑（.npz）；None 則跳過 store-matching
        threshold:         魯肉飯判定門檻（預設 0.6）
        store_notes_path:  store_notes.json 路徑；None 則使用預設路徑

    Returns:
        (大叔回應字串, 辨識到的店家名稱或 None)
        店家名稱為 None 表示非魯肉飯或無比對結果
    """
    t_start = time.perf_counter()

    # 1. 前處理
    pil_img = preprocess(image_source)
    if pil_img is None:
        raise ValueError(f"無法讀取圖片：{image_source}")
    logger.info("[timing] preprocess: %.3fs", time.perf_counter() - t_start)

    # 2. 視覺辨識（含碗特徵，單次 Haiku call）
    t1 = time.perf_counter()
    visual = visual_recognize(pil_img, threshold=threshold)
    logger.info("[timing] visual_recognize: %.3fs", time.perf_counter() - t1)

    # 3. 店家比對（僅在確認為魯肉飯且有索引時執行）
    matching: MatchingResult = MatchingResult(is_tie=False, matches=[])
    if visual["is_lu_rou_fan"] and index_path:
        index_file = Path(index_path)
        if index_file.exists():
            t2 = time.perf_counter()
            index = load_index(str(index_file))
            from src import clip_model
            img_feat = clip_model.encode_image(pil_img).squeeze().numpy()
            logger.info("[timing] clip_encode: %.3fs", time.perf_counter() - t2)

            # 載入 store_notes 供 Haiku override 使用
            notes_file = Path(store_notes_path) if store_notes_path else _DEFAULT_STORE_NOTES
            store_notes = None
            if notes_file.exists():
                with open(notes_file, encoding="utf-8") as f:
                    store_notes = json.load(f)
            else:
                logger.warning("store_notes 不存在：%s，跳過 Haiku override", notes_file)

            haiku_features = {
                "bowl_color": visual.get("bowl_color"),
                "bowl_shape": visual.get("bowl_shape"),
                "bowl_texture": visual.get("bowl_texture"),
                "toppings": visual.get("toppings", []),
            }

            t3 = time.perf_counter()
            matching = match_store(
                img_feat, index,
                haiku_features=haiku_features,
                store_notes=store_notes,
                query_image=pil_img,
            )
            logger.info("[timing] match_store: %.3fs", time.perf_counter() - t3)
        else:
            logger.warning("索引檔不存在：%s，跳過店家比對", index_path)

    # 4. 大叔回應
    t4 = time.perf_counter()
    persona = _get_persona()
    response = persona.generate(visual, matching)
    logger.info("[timing] persona.generate: %.3fs", time.perf_counter() - t4)

    logger.info("[timing] total: %.3fs", time.perf_counter() - t_start)

    matched_store = None
    if visual.get("is_lu_rou_fan") and matching.get("matches"):
        matched_store = matching["matches"][0]["store_name"]

    return response, matched_store

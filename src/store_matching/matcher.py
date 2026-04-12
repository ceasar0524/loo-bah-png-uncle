"""
KNN 店家比對模組。
從向量索引找出最相似的店家，使用 photo-count 正規化投票決勝。
CLIP KNN 為主要信號；Haiku 偵測到高信心明確特徵時才覆蓋 CLIP 結果。
"""
import logging
import os
from collections import defaultdict
from typing import Optional

import numpy as np

from src.schemas import MatchingResult, StoreMatch

logger = logging.getLogger(__name__)

_DEFAULT_K = 5
_DEFAULT_THRESHOLD = 0.5
_HIGH_CONFIDENCE = 0.8
_TIE_MARGIN = 0.15  # 正規化票數差距在此範圍內視為平手

# Haiku 特徵覆蓋門檻與分數
_HAIKU_OVERRIDE_THRESHOLD = 0.75
_DINO_CONFIRM_THRESHOLD = 0.65  # 確認第一名（不換位）的信心門檻
_DINO_SWAP_THRESHOLD = 0.80    # 換位（第二名提至第一）的信心門檻
_BOWL_COLOR_SCORE = 0.5
_BOWL_SHAPE_SCORE = 0.2
_BOWL_TEXTURE_SCORE = 0.3
_CILANTRO_SCORE = 0.8
_TOPPING_SCORE = 0.3


def haiku_override(features: dict, store_notes: dict) -> tuple:
    """
    Haiku 特徵覆蓋判定。

    比對碗特徵（僅 distinctive 店家）與香菜配料，計算各店家得分。
    只有單一店家達門檻時才覆蓋 CLIP 結果；多家達標則抑制覆蓋。

    Args:
        features: classifier 回傳的特徵 dict（bowl_color、bowl_shape、bowl_texture、toppings）
        store_notes: data/store_notes.json 的內容

    Returns:
        (store_name, score) 若有明確勝出者；否則 (None, 0.0)
    """
    bowl_color = features.get("bowl_color")
    bowl_shape = features.get("bowl_shape")
    bowl_texture = features.get("bowl_texture")
    toppings = set(features.get("toppings") or [])

    scores: dict[str, float] = {}

    for store_name, data in store_notes.items():
        score = 0.0
        bowl = data.get("bowl", {})
        if bowl.get("distinctive"):
            if bowl.get("color") and bowl["color"] == bowl_color:
                score += _BOWL_COLOR_SCORE
            if bowl.get("shape") and bowl["shape"] == bowl_shape:
                score += _BOWL_SHAPE_SCORE
            if bowl.get("texture") and bowl["texture"] == bowl_texture:
                score += _BOWL_TEXTURE_SCORE

        known_toppings = set(data.get("known_toppings", []))
        for t in known_toppings & toppings:
            score += _CILANTRO_SCORE if t == "cilantro" else _TOPPING_SCORE

        if score >= _HAIKU_OVERRIDE_THRESHOLD:
            scores[store_name] = score

    if not scores:
        return None, 0.0

    max_score = max(scores.values())
    tied = [s for s, v in scores.items() if max_score - v < 0.05]
    if len(tied) > 1:
        logger.debug("haiku_override: tie among %s, suppressing override", tied)
        return None, 0.0

    winner = max(scores, key=scores.get)
    logger.debug("haiku_override: %s score=%.2f", winner, scores[winner])
    return winner, scores[winner]


def _sauce_consistency_tiebreak(
    candidates: list,
    store_notes: Optional[dict],
    query_image,
) -> tuple[list, bool]:
    """
    DINOv2 濃稠度 tiebreak：前兩名 sauce_consistency 標記不同時，
    預測 query 圖片的類別並將吻合者提至第一名。
    任何條件不符則回傳原 candidates 不變。

    Returns:
        (candidates, swapped) — swapped=True 表示有換位，可將 is_tie 改為 False
    """
    if len(candidates) < 2 or store_notes is None or query_image is None:
        return candidates, False

    c0 = store_notes.get(candidates[0]["store_name"], {}).get("sauce_consistency")
    c1 = store_notes.get(candidates[1]["store_name"], {}).get("sauce_consistency")

    if not c0 or not c1 or c0 == c1:
        return candidates, False

    logger.info(
        "sauce_consistency tiebreak: 前兩名 %s(%s) vs %s(%s)",
        candidates[0]["store_name"], c0, candidates[1]["store_name"], c1,
    )

    try:
        from src.sauce_consistency import predict_consistency
        result = predict_consistency(query_image)
    except Exception as e:
        logger.warning("sauce_consistency tiebreak 失敗：%s", e)
        return candidates, False

    if result is None:
        return candidates, False

    prediction, confidence = result
    logger.info("sauce_consistency tiebreak: 預測=%s confidence=%.2f", prediction, confidence)

    if c1 == prediction and c0 != prediction:
        if confidence >= _DINO_SWAP_THRESHOLD:
            logger.info(
                "sauce_consistency tiebreak: 將 %s(%s) 提至第一（預測=%s confidence=%.2f）",
                candidates[1]["store_name"], c1, prediction, confidence,
            )
            return [candidates[1], candidates[0]] + candidates[2:], True
        logger.info(
            "sauce_consistency tiebreak: 換位信心不足（%.2f < %.2f），不換位",
            confidence, _DINO_SWAP_THRESHOLD,
        )
        return candidates, False

    # 第一名已吻合，確認無誤
    if c0 == prediction:
        if confidence >= _DINO_CONFIRM_THRESHOLD:
            logger.info(
                "sauce_consistency tiebreak: 確認 %s(%s) 維持第一（預測=%s confidence=%.2f）",
                candidates[0]["store_name"], c0, prediction, confidence,
            )
            return candidates, True
        logger.info(
            "sauce_consistency tiebreak: 確認信心不足（%.2f < %.2f），保持平手",
            confidence, _DINO_CONFIRM_THRESHOLD,
        )
        return candidates, False

    return candidates, False


def match_store(
    query_vector: np.ndarray,
    index: dict,
    k: int = _DEFAULT_K,
    threshold: float = _DEFAULT_THRESHOLD,
    haiku_features: Optional[dict] = None,
    store_notes: Optional[dict] = None,
    query_image=None,
) -> MatchingResult:
    """
    KNN 比對：找出最像的店家。CLIP 為主，Haiku 特徵高信心時覆蓋。

    Args:
        query_vector:   L2 正規化的查詢向量（shape: (D,)）
        index:          load_index() 回傳的字典，含 vectors、labels、photo_counts
        k:              top-K 鄰居數，預設 5
        threshold:      相似度門檻，預設 0.5，低於此值回傳空 list
        haiku_features: classifier 回傳的碗與配料特徵（可選）
        store_notes:    store_notes.json 內容（haiku_features 存在時必須提供）

    Returns:
        MatchingResult: {is_tie, matches}
    """
    vectors: np.ndarray = index["vectors"]   # (N, D)
    labels: list = index["labels"]           # (N,)
    photo_counts: dict = index["photo_counts"]  # {store_name: count}

    # 餘弦相似度（向量已 L2 正規化，點積即餘弦）
    similarities = vectors @ query_vector    # (N,)

    # 取 top-K 索引（降序）
    actual_k = min(k, len(similarities))
    top_indices = np.argpartition(similarities, -actual_k)[-actual_k:]
    top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

    # 計算各店家：raw votes 和對應的相似度列表
    store_votes: dict[str, int] = defaultdict(int)
    store_sims: dict[str, list] = defaultdict(list)

    for idx in top_indices:
        store = labels[idx]
        store_votes[store] += 1
        store_sims[store].append(float(similarities[idx]))

    # photo-count 正規化投票
    store_normalized: dict[str, float] = {}
    for store, raw_votes in store_votes.items():
        count = photo_counts.get(store, 1)
        store_normalized[store] = raw_votes / count

    # 找最高正規化票數
    max_norm_vote = max(store_normalized.values())

    # 平手判定：差距在 _TIE_MARGIN 內視為平手
    tied_stores = [s for s, v in store_normalized.items() if max_norm_vote - v <= _TIE_MARGIN]
    is_tie = len(tied_stores) > 1

    if is_tie:
        # 平手：計算各店家 Haiku 特徵分，加上 CLIP 相似度排序
        haiku_scores: dict[str, float] = {}
        if haiku_features and store_notes:
            toppings = set(haiku_features.get("toppings") or [])
            bowl_color = haiku_features.get("bowl_color")
            bowl_shape = haiku_features.get("bowl_shape")
            bowl_texture = haiku_features.get("bowl_texture")
            for store in tied_stores:
                score = 0.0
                data = store_notes.get(store, {})
                known_toppings = set(data.get("known_toppings", []))
                for t in known_toppings & toppings:
                    score += _CILANTRO_SCORE if t == "cilantro" else _TOPPING_SCORE
                bowl = data.get("bowl", {})
                if bowl.get("distinctive"):
                    if bowl.get("color") and bowl["color"] == bowl_color:
                        score += _BOWL_COLOR_SCORE
                    if bowl.get("shape") and bowl["shape"] == bowl_shape:
                        score += _BOWL_SHAPE_SCORE
                    if bowl.get("texture") and bowl["texture"] == bowl_texture:
                        score += _BOWL_TEXTURE_SCORE
                haiku_scores[store] = score

        candidates = []
        for store in tied_stores:
            avg_sim = float(np.mean(store_sims[store]))
            count = photo_counts.get(store, 0)
            level = _confidence_level(avg_sim)
            candidates.append(StoreMatch(
                store_name=store,
                similarity=avg_sim,
                confidence_level=level,
                photo_count=count,
            ))
        candidates.sort(
            key=lambda x: (haiku_scores.get(x["store_name"], 0.0), x["similarity"]),
            reverse=True,
        )

        # Sauce consistency tiebreak（第三層）：僅在 DINO_TIEBREAK_ENABLED=true 且前兩名標記不同時啟動
        tiebreak_resolved = False
        if os.getenv("DINO_TIEBREAK_ENABLED", "false").lower() == "true":
            candidates, tiebreak_resolved = _sauce_consistency_tiebreak(candidates, store_notes, query_image)

        return MatchingResult(is_tie=not tiebreak_resolved, matches=candidates)

    # 唯一勝出店家
    winner = tied_stores[0]
    avg_sim = float(np.mean(store_sims[winner]))

    # 門檻過濾
    if avg_sim < threshold:
        logger.info("similarity %.3f below threshold %.3f, no match", avg_sim, threshold)
        return MatchingResult(is_tie=False, matches=[])

    count = photo_counts.get(winner, 0)
    level = _confidence_level(avg_sim)
    match = StoreMatch(
        store_name=winner,
        similarity=avg_sim,
        confidence_level=level,
        photo_count=count,
    )
    clip_result = MatchingResult(is_tie=False, matches=[match])

    # Haiku 特徵覆蓋後處理
    if haiku_features and store_notes:
        override_store, override_score = haiku_override(haiku_features, store_notes)
        if override_store is not None:
            override_count = photo_counts.get(override_store, 0)
            override_match = StoreMatch(
                store_name=override_store,
                similarity=avg_sim,
                confidence_level="high",
                photo_count=override_count,
            )
            logger.info(
                "haiku_override: %s (score=%.2f) overrides CLIP winner %s",
                override_store, override_score, winner,
            )
            return MatchingResult(is_tie=False, matches=[override_match])

    return clip_result


def _confidence_level(similarity: float) -> str:
    if similarity >= _HIGH_CONFIDENCE:
        return "high"
    return "medium"
